"""Assignments router: create, list, and complete assignments."""

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth0 import get_current_user
from app.db.database import get_db
from app.models.assignment import Assignment
from app.models.need import Need
from app.models.volunteer import Volunteer
from app.schemas.assignment import AssignmentCreate, AssignmentComplete, AssignmentResponse
from app.services import embedding_service, alert_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentResponse, status_code=201)
async def create_assignment(
    body: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Assign a volunteer to a community need.
    Calculates match_score, updates need status, sends alert.
    """
    need = db.query(Need).filter(Need.id == body.need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    volunteer = db.query(Volunteer).filter(Volunteer.id == body.volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    if need.status != "open":
        raise HTTPException(status_code=400, detail=f"Need is already {need.status}")

    # Calculate match score
    match_score = 0.5
    if volunteer.embedding and need.embedding:
        skill_sim = embedding_service.cosine_similarity(
            list(volunteer.embedding), list(need.embedding)
        )
        match_score = round(0.5 * skill_sim + 0.5 * 0.7, 4)

    assignment = Assignment(
        need_id=body.need_id,
        volunteer_id=body.volunteer_id,
        status="pending",
        match_score=match_score,
    )
    db.add(assignment)

    # Update need status
    need.status = "assigned"
    db.commit()
    db.refresh(assignment)

    logger.info(f"Assignment created: volunteer {volunteer.name} → need {need.need_type}")

    # Send assignment confirmation alert
    await alert_service.broadcast_alert({
        "type": "assignment_created",
        "assignment_id": str(assignment.id),
        "need_id": str(need.id),
        "volunteer_name": volunteer.name,
        "need_type": need.need_type,
        "district": need.location_district,
        "match_score": match_score,
    })

    return assignment


@router.get("", response_model=List[AssignmentResponse])
def list_assignments(
    status: str = None,
    db: Session = Depends(get_db),
):
    """List all assignments, optionally filtered by status."""
    query = db.query(Assignment)
    if status:
        query = query.filter(Assignment.status == status)
    return query.order_by(Assignment.assigned_at.desc()).all()


@router.put("/{assignment_id}/complete", response_model=AssignmentResponse)
def complete_assignment(
    assignment_id: UUID,
    body: AssignmentComplete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Mark an assignment as complete with outcome notes.
    Updates volunteer metrics and need status.
    """
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.status = "completed"
    assignment.outcome_notes = body.outcome_notes
    assignment.volunteer_rating = body.volunteer_rating
    assignment.completed_at = datetime.now(timezone.utc)

    # Update need status
    need = db.query(Need).filter(Need.id == assignment.need_id).first()
    if need:
        need.status = "resolved"

    # Update volunteer metrics
    volunteer = db.query(Volunteer).filter(Volunteer.id == assignment.volunteer_id).first()
    if volunteer:
        volunteer.total_tasks_completed = (volunteer.total_tasks_completed or 0) + 1
        if body.volunteer_rating:
            prior_total = (volunteer.average_rating or 0) * max((volunteer.total_tasks_completed or 1) - 1, 0)
            volunteer.average_rating = round(
                (prior_total + body.volunteer_rating) / volunteer.total_tasks_completed, 2
            )

    db.commit()
    db.refresh(assignment)
    logger.info(f"Assignment {assignment_id} completed")
    return assignment

"""Volunteers router: registration, listing, and semantic matching."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth0 import get_current_user
from app.db.database import get_db
from app.models.volunteer import Volunteer
from app.schemas.volunteer import VolunteerCreate, VolunteerResponse, MatchResponse
from app.services import embedding_service
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(tags=["volunteers"])


@router.get("/volunteers", response_model=List[VolunteerResponse])
def list_volunteers(db: Session = Depends(get_db)):
    """List all registered volunteers."""
    return db.query(Volunteer).all()


@router.get("/volunteers/{volunteer_id}", response_model=VolunteerResponse)
def get_volunteer(volunteer_id: UUID, db: Session = Depends(get_db)):
    """Get a single volunteer by ID."""
    vol = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not vol:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    return vol


@router.post("/volunteers", response_model=VolunteerResponse, status_code=201)
def create_volunteer(
    body: VolunteerCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Register a new volunteer.
    Automatically generates skill embedding for semantic matching.
    """
    # Check for duplicate email
    existing = db.query(Volunteer).filter(Volunteer.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Parse skills from free-form text
    skills_list = [s.strip() for s in body.skills_raw.replace(",", " ").split() if len(s.strip()) > 2]

    volunteer = Volunteer(
        name=body.name,
        email=body.email,
        phone=body.phone,
        skills_raw=body.skills_raw,
        skills_list=skills_list,
        availability=body.availability or {},
        transport_available=body.transport_available,
        latitude=body.latitude,
        longitude=body.longitude,
        willing_distance_km=body.willing_distance_km,
        total_tasks_completed=0,
        average_rating=0.0,
    )

    # Generate and store embedding
    embedding = embedding_service.embed_volunteer({
        "skills_raw": body.skills_raw,
        "skills_list": skills_list,
    })
    volunteer.embedding = embedding

    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    logger.info(f"Volunteer registered: {volunteer.name} ({volunteer.email})")
    return volunteer


@router.get("/matches/{volunteer_id}", response_model=List[MatchResponse])
def get_matches_for_volunteer(
    volunteer_id: UUID,
    top_k: int = 5,
    db: Session = Depends(get_db),
):
    """
    Return the top-K community needs that best match a volunteer's skills.
    Uses the PRD semantic matching formula:
    match_score = (0.5 × skill_similarity) + (0.3 × availability_match) + (0.2 × (1 - distance_decay))
    """
    volunteer = db.query(Volunteer).filter(Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    matches = embedding_service.find_matching_needs_for_volunteer(db, volunteer, top_k=top_k)

    results = []
    for m in matches:
        need = m["need"]
        results.append(MatchResponse(
            need_id=need.id,
            need_type=need.need_type,
            urgency=need.urgency,
            location_district=need.location_district,
            location_address=need.location_address,
            skills_needed=need.skills_needed,
            affected_population=need.affected_population,
            estimated_effort_hours=need.estimated_effort_hours,
            urgency_score=need.urgency_score,
            match_score=m["match_score"],
            skill_similarity=m["skill_similarity"],
            status=need.status,
            created_at=need.created_at,
        ))
    return results

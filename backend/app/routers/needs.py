"""Needs router: list, filter, and detail endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.need import Need
from app.schemas.need import NeedResponse, NeedListResponse
from app.services import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/needs", tags=["needs"])


@router.get("", response_model=NeedListResponse)
def list_needs(
    urgency: Optional[str] = Query(None, description="Filter: CRITICAL, HIGH, MEDIUM, LOW"),
    need_type: Optional[str] = Query(None, description="Filter by need type"),
    district: Optional[str] = Query(None),
    status: Optional[str] = Query("open"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Return prioritized needs feed, sorted by urgency_score DESC.
    Supports filtering by urgency, type, district, and status.
    """
    query = db.query(Need)

    if status:
        query = query.filter(Need.status == status)
    if urgency:
        query = query.filter(Need.urgency == urgency.upper())
    if need_type:
        query = query.filter(Need.need_type.ilike(f"%{need_type}%"))
    if district:
        query = query.filter(Need.location_district.ilike(f"%{district}%"))

    query = query.filter(Need.duplicate_of.is_(None))   # exclude raw duplicates

    total = query.count()
    needs = query.order_by(desc(Need.urgency_score)).offset(skip).limit(limit).all()

    return NeedListResponse(total=total, needs=needs)


@router.get("/{need_id}", response_model=NeedResponse)
def get_need_detail(
    need_id: UUID,
    include_recommendations: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Get full details of a single need.
    Optionally generates LLM recommendations via Claude.
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Need not found")

    response = NeedResponse.model_validate(need)

    if include_recommendations and need.status == "open":
        need_dict = {
            "need_type": need.need_type,
            "urgency": need.urgency,
            "urgency_reason": need.urgency_reason,
            "skills_needed": need.skills_needed,
            "location_district": need.location_district,
            "affected_population": need.affected_population,
            "resource_gaps": need.resource_gaps,
        }
        response.recommendations = llm_service.generate_recommendations(need_dict)

    return response

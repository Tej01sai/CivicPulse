"""Pydantic schemas for assignments."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    """Request body to create an assignment."""
    need_id: UUID
    volunteer_id: UUID


class AssignmentComplete(BaseModel):
    """Request body to mark assignment complete."""
    outcome_notes: Optional[str] = None
    volunteer_rating: Optional[float] = None   # 1.0 – 5.0


class AssignmentResponse(BaseModel):
    """Assignment record returned from DB."""
    id: UUID
    need_id: UUID
    volunteer_id: UUID
    status: str
    match_score: Optional[float]
    outcome_notes: Optional[str]
    volunteer_rating: Optional[float]
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

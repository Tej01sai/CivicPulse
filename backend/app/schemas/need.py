"""Pydantic schemas for community needs."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel


class ParseRequest(BaseModel):
    """Request body for intake parsing."""
    text: str


class ParseResponse(BaseModel):
    """Structured need extracted by LLM."""
    need_type: Optional[str] = None
    need_subtype: Optional[str] = None
    beneficiary_age_range: Optional[str] = None
    location_address: Optional[str] = None
    location_district: Optional[str] = None
    urgency: Optional[str] = None
    urgency_reason: Optional[str] = None
    skills_needed: Optional[List[str]] = []
    affected_population: Optional[int] = 1
    resource_gaps: Optional[str] = None
    estimated_effort_hours: Optional[float] = None
    confidence_score: Optional[float] = None
    raw_input: Optional[str] = None


class NeedCreate(ParseResponse):
    """Used internally when storing a parsed need."""
    pass


class NeedResponse(BaseModel):
    """Full need record returned from DB."""
    id: UUID
    raw_input: Optional[str]
    need_type: Optional[str]
    need_subtype: Optional[str]
    location_address: Optional[str]
    location_district: Optional[str]
    urgency: Optional[str]
    urgency_reason: Optional[str]
    skills_needed: Optional[List[str]]
    affected_population: Optional[int]
    resource_gaps: Optional[str]
    estimated_effort_hours: Optional[float]
    escalation_risk: Optional[float]
    urgency_score: Optional[float]
    confidence_score: Optional[float]
    status: Optional[str]
    report_count: Optional[int]
    duplicate_of: Optional[UUID]
    created_at: Optional[datetime]
    recommendations: Optional[str] = None   # LLM-generated, not in DB

    class Config:
        from_attributes = True


class NeedListResponse(BaseModel):
    """Paginated list of needs."""
    total: int
    needs: List[NeedResponse]

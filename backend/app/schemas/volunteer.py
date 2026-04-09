"""Pydantic schemas for volunteers and skill matching."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel


class VolunteerCreate(BaseModel):
    """Request body to register a volunteer."""
    name: str
    email: str
    phone: Optional[str] = None
    skills_raw: str                          # free-form text: "I do carpentry, roofing..."
    availability: Optional[Dict[str, Any]] = {}
    transport_available: Optional[bool] = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    willing_distance_km: Optional[float] = 10.0


class VolunteerResponse(BaseModel):
    """Volunteer profile returned from DB."""
    id: UUID
    name: str
    email: str
    phone: Optional[str]
    skills_raw: Optional[str]
    skills_list: Optional[List[str]]
    availability: Optional[Dict[str, Any]]
    transport_available: Optional[bool]
    latitude: Optional[float]
    longitude: Optional[float]
    willing_distance_km: Optional[float]
    total_tasks_completed: Optional[int]
    average_rating: Optional[float]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    """A volunteer-need match result."""
    need_id: UUID
    need_type: Optional[str]
    urgency: Optional[str]
    location_district: Optional[str]
    location_address: Optional[str]
    skills_needed: Optional[List[str]]
    affected_population: Optional[int]
    estimated_effort_hours: Optional[float]
    urgency_score: Optional[float]
    match_score: float                       # 0.0 – 1.0
    skill_similarity: float
    status: Optional[str]
    created_at: Optional[datetime]

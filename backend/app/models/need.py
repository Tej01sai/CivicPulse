"""Need model for community needs data."""

from datetime import datetime
from uuid import uuid4
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ARRAY, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Need(Base):
    """Community need record."""

    __tablename__ = "needs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    raw_input = Column(Text)

    # Extracted fields
    need_type = Column(String(50))
    need_subtype = Column(String(100))
    location_address = Column(Text)
    location_district = Column(String(50))
    urgency = Column(String(20))
    urgency_reason = Column(Text)
    skills_needed = Column(ARRAY(String))
    affected_population = Column(Integer, default=1)
    resource_gaps = Column(Text)
    estimated_effort_hours = Column(Float)

    # Scoring and metrics
    escalation_risk = Column(Float, default=0.5)
    urgency_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)

    # Status and deduplication
    status = Column(String(20), default="open")
    duplicate_of = Column(UUID(as_uuid=True), ForeignKey("needs.id"), nullable=True)
    report_count = Column(Integer, default=1)

    # Embeddings
    embedding = Column(Vector(384))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Need {self.id} {self.need_type} {self.urgency}>"

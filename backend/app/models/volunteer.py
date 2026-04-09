"""Volunteer model for volunteer profiles and availability."""

from datetime import datetime
from uuid import uuid4
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Float, DateTime, Text, ARRAY, JSON, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Volunteer(Base):
    """Volunteer profile and skills."""

    __tablename__ = "volunteers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))

    # Skills
    skills_raw = Column(Text)
    skills_list = Column(ARRAY(String))

    # Availability and location
    availability = Column(JSON, default={})
    transport_available = Column(Boolean, default=False)
    latitude = Column(Float)
    longitude = Column(Float)
    willing_distance_km = Column(Float, default=10.0)

    # Embeddings
    embedding = Column(Vector(384))

    # Metrics
    total_tasks_completed = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<Volunteer {self.name} {self.skills_list}>"

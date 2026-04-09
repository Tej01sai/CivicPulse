"""Assignment model for volunteer-to-need assignments."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, Float, DateTime, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Assignment(Base):
    """Assignment of a volunteer to a community need."""

    __tablename__ = "assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    need_id = Column(UUID(as_uuid=True), ForeignKey("needs.id"))
    volunteer_id = Column(UUID(as_uuid=True), ForeignKey("volunteers.id"))

    # Assignment details
    status = Column(String(20), default="pending")
    match_score = Column(Float)

    # Outcome
    outcome_notes = Column(Text)
    volunteer_rating = Column(Float, nullable=True)

    # Timestamps
    assigned_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Assignment {self.id} {self.status}>"

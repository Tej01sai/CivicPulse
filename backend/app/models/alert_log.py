"""AlertLog model for tracking sent alerts."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class AlertLog(Base):
    """Record of alerts sent for critical needs."""

    __tablename__ = "alert_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    need_id = Column(UUID(as_uuid=True), ForeignKey("needs.id"))

    alert_type = Column(String(50))          # "sms", "in_app", "email"
    message = Column(Text)
    channels_sent = Column(String(200))      # comma-separated: "sms,in_app"
    recipient = Column(String(200))          # phone or email or "all_volunteers"

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<AlertLog {self.id} {self.alert_type} need={self.need_id}>"

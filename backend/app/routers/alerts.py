"""Alerts router: manual alert trigger for coordinators."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.auth0 import get_current_user
from app.db.database import get_db
from app.models.need import Need
from app.services import alert_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/trigger/{need_id}")
async def trigger_alert_manual(
    need_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Manually trigger an alert for a specific need.
    Sends SMS to coordinator + broadcasts WebSocket to all clients.
    """
    need = db.query(Need).filter(Need.id == need_id).first()
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    await alert_service.trigger_alert(need, db)
    return {"status": "alert_sent", "need_id": str(need_id)}


@router.get("/stats")
def get_alert_stats(db: Session = Depends(get_db)):
    """Return summary stats for the dashboard header."""
    from app.models.need import Need
    from sqlalchemy import func

    total_open = db.query(Need).filter(Need.status == "open").count()
    critical = db.query(Need).filter(
        Need.status == "open", Need.urgency == "CRITICAL"
    ).count()
    high = db.query(Need).filter(
        Need.status == "open", Need.urgency == "HIGH"
    ).count()
    resolved_today = db.query(Need).filter(Need.status == "resolved").count()

    from app.models.volunteer import Volunteer
    total_volunteers = db.query(Volunteer).count()

    from app.models.assignment import Assignment
    total_assignments = db.query(Assignment).count()
    completed = db.query(Assignment).filter(Assignment.status == "completed").count()
    match_rate = round(completed / total_assignments * 100, 1) if total_assignments else 0

    return {
        "total_open_needs": total_open,
        "critical_needs": critical,
        "high_needs": high,
        "resolved_total": resolved_today,
        "total_volunteers": total_volunteers,
        "total_assignments": total_assignments,
        "match_success_rate": match_rate,
    }

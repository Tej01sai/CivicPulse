"""Alert service: SMS via Twilio + WebSocket in-app notifications."""

import logging
from typing import TYPE_CHECKING, Dict, Set
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.alert_log import AlertLog
from app.models.need import Need

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = logging.getLogger(__name__)
settings = get_settings()

# In-memory WebSocket connection registry: {ws_id: WebSocket}
active_connections: Dict[str, "WebSocket"] = {}

URGENCY_SCORE_THRESHOLD = 0.75
DAYS_PENDING_MAX = 3
ESCALATION_RISK_THRESHOLD = 0.6


def should_alert(need: Need) -> bool:
    """
    PRD logic:
    is_critical = (urgency_score > 0.75) AND
                  (days_pending < 3) AND
                  (escalation_risk > 0.6)
    """
    from datetime import datetime, timezone
    if need.urgency_score is None or need.escalation_risk is None:
        return need.urgency in ("CRITICAL",)

    created = need.created_at
    if created and created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - created).days if created else 0

    return (
        need.urgency_score > URGENCY_SCORE_THRESHOLD and
        days < DAYS_PENDING_MAX and
        need.escalation_risk > ESCALATION_RISK_THRESHOLD
    )


def _send_sms(to: str, message: str) -> bool:
    """Send SMS via Twilio. No-op if credentials not configured."""
    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=message,
            from_=settings.twilio_from_number,
            to=to
        )
        logger.info(f"SMS sent to {to}")
        return True
    except Exception as e:
        logger.warning(f"SMS skipped (Twilio not configured or error): {e}")
        return False


async def broadcast_alert(message: dict):
    """Broadcast alert to all connected WebSocket clients."""
    import json
    disconnected = []
    for ws_id, ws in active_connections.items():
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            disconnected.append(ws_id)
    for ws_id in disconnected:
        active_connections.pop(ws_id, None)


async def trigger_alert(need: Need, db: Session):
    """
    Main alert dispatch function:
    1. Send SMS to coordinator
    2. Broadcast WebSocket to all connected frontend clients
    3. Log alert to DB
    """
    district = need.location_district or "Unknown District"
    need_type = need.need_type or "Community Need"
    urgency = need.urgency or "HIGH"

    sms_message = (
        f"🚨 {urgency}: {need_type} in {district}. "
        f"{need.affected_population or 1} affected. "
        f"Tap to respond: {settings.backend_url}/needs/{need.id}"
    )

    # 1. SMS to coordinator
    sms_sent = _send_sms(settings.coordinator_phone, sms_message)

    # 2. In-app WebSocket broadcast
    ws_payload = {
        "type": "critical_alert",
        "need_id": str(need.id),
        "need_type": need_type,
        "urgency": urgency,
        "district": district,
        "message": sms_message,
        "urgency_score": need.urgency_score,
    }
    await broadcast_alert(ws_payload)

    # 3. Log to DB
    channels = ["in_app"]
    if sms_sent:
        channels.append("sms")

    log = AlertLog(
        need_id=need.id,
        alert_type="critical",
        message=sms_message,
        channels_sent=",".join(channels),
        recipient=settings.coordinator_phone,
    )
    db.add(log)
    db.commit()
    logger.info(f"Alert triggered for need {need.id} via {channels}")

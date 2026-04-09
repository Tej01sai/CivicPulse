"""Ranking service: urgency score calculation per PRD formula."""

import logging
import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.need import Need

logger = logging.getLogger(__name__)

# Urgency tier to numeric mapping
URGENCY_MAP = {
    "CRITICAL": 1.0,
    "HIGH": 0.75,
    "MEDIUM": 0.5,
    "LOW": 0.25,
}


def calculate_urgency_score(need: Need) -> float:
    """
    PRD formula:
    urgency_score = (0.4 × reported_urgency) +
                    (0.3 × affected_population_log) +
                    (0.2 × escalation_risk) +
                    (0.1 × days_pending_normalized)
    """
    reported_urgency = URGENCY_MAP.get(need.urgency or "MEDIUM", 0.5)

    # Log-normalize population (max reasonable = 1000)
    pop = max(1, need.affected_population or 1)
    affected_population_log = min(math.log10(pop) / 3.0, 1.0)

    escalation_risk = need.escalation_risk or 0.5

    # Days pending: 0 days = 0, 14+ days = 1.0
    if need.created_at:
        now = datetime.now(timezone.utc)
        created = need.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        days = (now - created).days
    else:
        days = 0
    days_pending_normalized = min(days / 14.0, 1.0)

    score = (
        0.4 * reported_urgency +
        0.3 * affected_population_log +
        0.2 * escalation_risk +
        0.1 * days_pending_normalized
    )
    return round(min(score, 1.0), 4)


def recalculate_all_scores(db: Session) -> int:
    """Recalculate urgency scores for all open needs. Returns count updated."""
    needs = db.query(Need).filter(Need.status == "open").all()
    updated = 0
    for need in needs:
        new_score = calculate_urgency_score(need)
        if abs((need.urgency_score or 0.0) - new_score) > 0.001:
            need.urgency_score = new_score
            updated += 1
    db.commit()
    logger.info(f"Recalculated urgency scores: {updated}/{len(needs)} updated")
    return updated

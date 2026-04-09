"""Intake router: parse unstructured field notes or survey images via Claude."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.auth.auth0 import get_current_user
from app.db.database import get_db
from app.models.need import Need
from app.schemas.need import ParseRequest, ParseResponse, NeedResponse
from app.services import embedding_service, llm_service, ranking_service, alert_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/intake", tags=["intake"])


def _store_need(db: Session, parsed: dict) -> Need:
    """Embed the parsed need, check for duplicates, then store."""
    embedding = embedding_service.embed_need(parsed)

    # Deduplication check
    similar = embedding_service.find_similar_needs(db, embedding, threshold=0.85)
    if similar:
        # Increment the existing need's report count
        existing = similar[0]
        existing.report_count = (existing.report_count or 1) + 1
        db.commit()
        db.refresh(existing)
        logger.info(f"Duplicate detected — incremented need {existing.id} count to {existing.report_count}")
        return existing

    # Sanitize skills field
    skills = parsed.get("skills_needed", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]

    # Create new need record
    need = Need(
        raw_input=parsed.get("raw_input", ""),
        need_type=parsed.get("need_type"),
        need_subtype=parsed.get("need_subtype"),
        location_address=parsed.get("location_address"),
        location_district=parsed.get("location_district"),
        urgency=parsed.get("urgency", "MEDIUM"),
        urgency_reason=parsed.get("urgency_reason"),
        skills_needed=skills,
        affected_population=parsed.get("affected_population", 1),
        resource_gaps=parsed.get("resource_gaps"),
        estimated_effort_hours=parsed.get("estimated_effort_hours"),
        confidence_score=parsed.get("confidence_score", 0.5),
        escalation_risk=0.5,
        status="open",
        report_count=1,
        embedding=embedding,
    )
    need.urgency_score = ranking_service.calculate_urgency_score(need)
    db.add(need)
    db.commit()
    db.refresh(need)

    # Optionally sync to Pinecone
    embedding_service.store_need_embedding_pinecone(
        str(need.id),
        embedding,
        {"need_type": need.need_type, "urgency": need.urgency, "district": need.location_district},
    )
    return need


@router.post("/parse", response_model=NeedResponse)
async def parse_text_intake(
    request: ParseRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Parse unstructured field notes into a structured community need.
    Runs deduplication before storing. Triggers alert if CRITICAL.
    """
    logger.info(f"Text intake: {len(request.text)} chars")
    parsed = llm_service.parse_need_from_text(request.text)
    need = _store_need(db, parsed)

    # Alert if critical
    if alert_service.should_alert(need):
        import asyncio
        asyncio.create_task(alert_service.trigger_alert(need, db))

    return need


@router.post("/parse-image", response_model=NeedResponse)
async def parse_image_intake(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Parse a survey photo or image via Claude Vision.
    Accepted types: image/jpeg, image/png, image/webp.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:   # 20MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 20MB)")

    logger.info(f"Image intake: {file.filename}, {len(image_bytes)} bytes")
    parsed = llm_service.parse_need_from_image(image_bytes, file.content_type)
    need = _store_need(db, parsed)

    if alert_service.should_alert(need):
        import asyncio
        asyncio.create_task(alert_service.trigger_alert(need, db))

    return need

"""Embedding service: Sentence-Transformers + pgvector + optional Pinecone."""

import logging
from typing import List, Optional
from uuid import UUID

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.need import Need
from app.models.volunteer import Volunteer

logger = logging.getLogger(__name__)
settings = get_settings()

# Singleton model (loaded once at startup)
_model: Optional[SentenceTransformer] = None


def get_model() -> SentenceTransformer:
    """Lazily load and cache the Sentence-Transformers model."""
    global _model
    if _model is None:
        logger.info("Loading Sentence-Transformers model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("✓ Sentence-Transformers model loaded")
    return _model


def embed_text(text_input: str) -> List[float]:
    """Embed a string into a 384-dim vector."""
    model = get_model()
    embedding = model.encode(text_input, normalize_embeddings=True)
    return embedding.tolist()


def _need_to_text(need_data: dict) -> str:
    """Convert need dict to a descriptive string for embedding."""
    parts = []
    if need_data.get("need_type"):
        parts.append(need_data["need_type"])
    if need_data.get("need_subtype"):
        parts.append(need_data["need_subtype"])
    if skills := need_data.get("skills_needed"):
        if isinstance(skills, list):
            parts.extend(skills)
    if need_data.get("urgency_reason"):
        parts.append(need_data["urgency_reason"])
    if need_data.get("resource_gaps"):
        parts.append(need_data["resource_gaps"])
    if need_data.get("raw_input"):
        parts.append(need_data["raw_input"][:300])   # truncate to 300 chars
    return " ".join(parts) if parts else "community need"


def embed_need(need_data: dict) -> List[float]:
    """Create embedding for a need record."""
    text_repr = _need_to_text(need_data)
    return embed_text(text_repr)


def embed_volunteer(volunteer_data: dict) -> List[float]:
    """Create embedding for a volunteer's skills."""
    parts = []
    if volunteer_data.get("skills_raw"):
        parts.append(volunteer_data["skills_raw"])
    if skills := volunteer_data.get("skills_list"):
        if isinstance(skills, list):
            parts.extend(skills)
    return embed_text(" ".join(parts) if parts else "volunteer")


def find_similar_needs(
    db: Session,
    embedding: List[float],
    threshold: float = 0.85,
    exclude_id: Optional[UUID] = None,
) -> List[Need]:
    """
    Query pgvector for needs with cosine similarity > threshold.
    Used for deduplication: if a similar need exists, we increment its count.
    """
    try:
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
        query = text("""
            SELECT id, (1 - (embedding <=> :vec::vector)) AS similarity
            FROM needs
            WHERE status = 'open'
              AND embedding IS NOT NULL
              AND (1 - (embedding <=> :vec::vector)) > :threshold
              AND (:exclude_id IS NULL OR id != :exclude_id::uuid)
            ORDER BY similarity DESC
            LIMIT 5
        """)
        rows = db.execute(query, {
            "vec": vec_str,
            "threshold": threshold,
            "exclude_id": str(exclude_id) if exclude_id else None
        }).fetchall()

        if not rows:
            return []
        ids = [row[0] for row in rows]
        return db.query(Need).filter(Need.id.in_(ids)).all()
    except Exception as e:
        logger.error(f"pgvector similarity search failed: {e}")
        return []


def store_need_embedding_pinecone(need_id: str, embedding: List[float], metadata: dict):
    """Store embedding in Pinecone (optional, skipped if not configured)."""
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(settings.pinecone_index_name)
        index.upsert(vectors=[(need_id, embedding, metadata)])
        logger.debug(f"Stored embedding in Pinecone for need {need_id}")
    except Exception as e:
        logger.warning(f"Pinecone upsert skipped: {e}")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Numpy cosine similarity between two vectors."""
    va, vb = np.array(a), np.array(b)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


def find_matching_needs_for_volunteer(
    db: Session,
    volunteer: Volunteer,
    top_k: int = 5,
) -> List[dict]:
    """
    PRD matching formula:
    match_score = (0.5 × skill_similarity) +
                  (0.3 × availability_match) +
                  (0.2 × (1 - distance_decay))
    """
    if volunteer.embedding is None:
        logger.warning(f"Volunteer {volunteer.id} has no embedding")
        return []

    vol_emb = list(volunteer.embedding)

    # Get all open needs with embeddings
    needs = db.query(Need).filter(
        Need.status == "open",
        Need.embedding.isnot(None)
    ).order_by(Need.urgency_score.desc()).limit(50).all()

    results = []
    for need in needs:
        need_emb = list(need.embedding)
        skill_sim = cosine_similarity(vol_emb, need_emb)

        # Availability match: simple heuristic (1.0 if availability dict not empty, else 0.7)
        availability_match = 0.7
        if volunteer.availability and isinstance(volunteer.availability, dict):
            availability_match = 1.0

        # Distance decay
        distance_decay = 0.5   # default when location unknown
        if (volunteer.latitude and volunteer.longitude and need.location_district):
            # Can't compute true distance without need lat/lng — use heuristic
            distance_decay = 0.2

        match_score = (
            0.5 * skill_sim +
            0.3 * availability_match +
            0.2 * (1 - distance_decay)
        )

        results.append({
            "need": need,
            "match_score": round(match_score, 4),
            "skill_similarity": round(skill_sim, 4),
        })

    # Sort by match_score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_k]

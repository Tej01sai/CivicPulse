"""
CivicPulse — Smart Resource Allocation API
FastAPI entry point with WebSocket support, CORS, and background score recalc.
"""

import asyncio
import json
import logging
import uuid

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import get_db
from app.db.init_db import init_db
from app.routers import intake, needs, volunteers, assignments, alerts
from app.services import alert_service, ranking_service

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("🚀 CivicPulse starting up...")

    # 1. Initialize DB tables
    init_db()

    # 2. Pre-load the Sentence-Transformers model (avoids cold start on first request)
    try:
        from app.services.embedding_service import get_model
        get_model()
    except Exception as e:
        logger.warning(f"Failed to pre-load embedding model: {e}")

    # 3. Start background urgency score recalculation (every 5 minutes)
    async def recalc_loop():
        while True:
            await asyncio.sleep(300)   # 5 minutes
            try:
                db_gen = get_db()
                db = next(db_gen)
                ranking_service.recalculate_all_scores(db)
                db_gen.close()
            except Exception as e:
                logger.error(f"Background recalc failed: {e}")

    asyncio.create_task(recalc_loop())
    logger.info("✓ Background urgency score recalculation started (every 5 min)")

    yield

    logger.info("CivicPulse shutting down")


app = FastAPI(
    title="CivicPulse — Smart Resource Allocation API",
    description="AI-powered NGO coordination platform: parse needs, match volunteers, trigger alerts.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.app_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(intake.router)
app.include_router(needs.router)
app.include_router(volunteers.router)
app.include_router(assignments.router)
app.include_router(alerts.router)


@app.get("/", tags=["health"])
def root():
    return {
        "name": "CivicPulse API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time in-app alerts.
    Each connected client receives critical need alerts and assignment updates.
    """
    ws_id = str(uuid.uuid4())
    await websocket.accept()
    alert_service.active_connections[ws_id] = websocket
    logger.info(f"WebSocket client connected: {ws_id} (total: {len(alert_service.active_connections)})")

    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "CivicPulse real-time alerts active",
            "client_id": ws_id,
        }))

        while True:
            # Keep connection alive (client can send ping)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        alert_service.active_connections.pop(ws_id, None)
        logger.info(f"WebSocket client disconnected: {ws_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        alert_service.active_connections.pop(ws_id, None)

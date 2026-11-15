import time
from collections import defaultdict
from typing import Dict, List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.assistant import AssistantQueryRequest, AssistantQueryResponse
from ai.mission_assistant import MissionAssistant

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])

# Simple in-memory sliding-window rate limiter per client IP
# Limit: 60 requests per 60-second window
RATE_LIMIT_MAX_REQUESTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60.0
_client_request_timestamps: Dict[str, List[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str):
    """Enforce per-IP rate limiting."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    # Filter timestamps within current sliding window
    timestamps = [t for t in _client_request_timestamps[client_ip] if t > cutoff]
    if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait a moment before sending additional queries.",
        )

    timestamps.append(now)
    _client_request_timestamps[client_ip] = timestamps


@router.post(
    "/query",
    response_model=AssistantQueryResponse,
    summary="Query the AI Mission Assistant",
    description="Ask planetary exploration, mission telemetry, or landing site questions. Grounded in official archives with citation provenance.",
)
def assistant_query(
    request_data: AssistantQueryRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    client_ip = req.client.host if req.client and req.client.host else "127.0.0.1"
    _check_rate_limit(client_ip)

    assistant = MissionAssistant(db=db)
    result = assistant.query(request_data.question)
    return result

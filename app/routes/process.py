import logging
from typing import Dict, Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/process")
async def trigger_process() -> Dict[str, Any]:
    """Manually trigger the processing pipeline.

    Phase 1 stub: logs the trigger and returns a confirmation.
    Phase 2 will wire Whisper transcription and LLM summarisation here.
    """
    logger.info("Manual trigger received via POST /api/process.")
    return {"status": "triggered", "message": "Processing pipeline triggered (Phase 1 stub)."}

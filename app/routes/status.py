import logging
from pathlib import Path as _Path
from typing import List

import jinja2
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

from app.database import get_session
from app.models import FileRecord

logger = logging.getLogger(__name__)

router = APIRouter()

# Build a Jinja2 Environment with cache_size=0 to avoid the LRUCache
# dict-key bug in Python 3.14 / Jinja2 3.x under Starlette 1.x.
_TEMPLATES_DIR = _Path(__file__).parent.parent / "templates"
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=jinja2.select_autoescape(["html"]),
    cache_size=0,  # disable bytecode cache to sidestep the LRUCache bug
)
templates = Jinja2Templates(env=_jinja_env)


@router.get("/api/status", response_model=List[FileRecord])
async def get_status(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> List[FileRecord]:
    """Return a paginated list of all FileRecords, newest first."""
    with get_session() as session:
        statement = (
            select(FileRecord)
            .order_by(FileRecord.uploaded_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        records = session.exec(statement).all()
        return list(records)


@router.get("/api/status/table", response_class=HTMLResponse)
async def status_table(request: Request) -> HTMLResponse:
    """Return an HTML table fragment for HTMX polling."""
    with get_session() as session:
        statement = (
            select(FileRecord)
            .order_by(FileRecord.uploaded_at.desc())  # type: ignore[union-attr]
            .limit(100)
        )
        records = session.exec(statement).all()

    return templates.TemplateResponse(
        request,
        "partials/status_table.html",
        {"records": records},
    )

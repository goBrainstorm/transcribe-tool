import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import select

from app.database import get_session
from app.models import FileRecord

logger = logging.getLogger(__name__)


async def delete_expired_files() -> None:
    """Delete local files whose retention window has elapsed.

    Targets FileRecords where:
      - status == "done"
      - delete_after <= now (UTC)
      - nextcloud_path is not None (confirmed backed up)

    Only the local copy is removed; the DB record is preserved.
    """
    now = datetime.now(timezone.utc)

    with get_session() as session:
        statement = select(FileRecord).where(
            FileRecord.status == "done",
            FileRecord.nextcloud_path.is_not(None),  # type: ignore[union-attr]
            FileRecord.delete_after <= now,  # type: ignore[operator]
        )
        expired_records = session.exec(statement).all()

        if not expired_records:
            logger.debug("Cleanup job: no expired files found.")
            return

        for record in expired_records:
            local = Path(record.local_path)
            if local.exists():
                try:
                    local.unlink()
                    logger.info(
                        "Deleted local file '%s' (FileRecord id=%s, backed up to '%s').",
                        record.local_path,
                        record.id,
                        record.nextcloud_path,
                    )
                except OSError as exc:
                    logger.error(
                        "Failed to delete local file '%s': %s",
                        record.local_path,
                        exc,
                    )
            else:
                logger.warning(
                    "Local file '%s' already absent for FileRecord id=%s.",
                    record.local_path,
                    record.id,
                )

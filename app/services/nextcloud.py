import logging
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def upload_file(local_path: str, remote_filename: str) -> str:
    """Upload a local file to Nextcloud via WebDAV PUT.

    Returns the remote path string on success.
    Returns an empty string if Nextcloud is not configured (NEXTCLOUD_URL unset).
    Raises httpx.HTTPStatusError on HTTP-level failures.
    """
    if not settings.nextcloud_url:
        logger.warning(
            "Nextcloud is not configured (NEXTCLOUD_URL is empty). "
            "Skipping upload of '%s'.",
            remote_filename,
        )
        return ""

    remote_dir = settings.nextcloud_remote_dir.strip("/")
    remote_path = f"{remote_dir}/{remote_filename}"
    dav_url = (
        f"{settings.nextcloud_url.rstrip('/')}"
        f"/remote.php/dav/files/{settings.nextcloud_user}"
        f"/{remote_path}"
    )

    file_bytes = Path(local_path).read_bytes()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.put(
            dav_url,
            content=file_bytes,
            auth=(settings.nextcloud_user, settings.nextcloud_pass),
            headers={"Content-Type": "application/octet-stream"},
        )
        response.raise_for_status()

    logger.info("Uploaded '%s' to Nextcloud at '%s'", local_path, remote_path)
    return remote_path

from typing import Any
from uuid import UUID

from server import clients

READ_PARAMS = "screenshot_id, file_name, file_type, file_size, download_url, created_at"


async def create(
    screenshot_id: UUID,
    file_name: str,
    file_type: str,
    file_size: int,
    download_url: str,
) -> dict[str, Any]:
    screenshot = await clients.database.fetch_one(
        query=f"""
            INSERT INTO screenshots (screenshot_id, file_name, file_type, file_size, download_url)
            VALUES (:screenshot_id, :file_name, :file_type, :file_size, :download_url)
            RETURNING {READ_PARAMS}
        """,
        values={
            "screenshot_id": screenshot_id,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
            "download_url": download_url,
        },
    )
    assert screenshot is not None
    return dict(screenshot._mapping)


async def fetch_one(screenshot_id: UUID) -> dict[str, Any] | None:
    screenshot = await clients.database.fetch_one(
        query=f"""
            SELECT {READ_PARAMS}
            FROM screenshots
            WHERE screenshot_id = :screenshot_id
        """,
        values={
            "screenshot_id": screenshot_id,
        },
    )
    return dict(screenshot._mapping) if screenshot is not None else None

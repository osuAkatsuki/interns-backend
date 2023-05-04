from typing import Any
from typing import cast
from typing import TypedDict
from uuid import UUID

from server import clients

READ_PARAMS = """\
    achievement_id,
    file_name,
    achievement_name,
    achievement_description
"""


class Achievement(TypedDict):
    achievement_id: UUID
    file_name: str
    achievement_name: str
    achievement_description: str


async def create(
    achievement_id: UUID,
    file_name: str,
    achievement_name: str,
    achievement_description: str,
) -> Achievement:
    achievement = await clients.database.fetch_one(
        query=f"""
            INSERT INTO achievements (achievement_id, file_name,achievement_name,achievement_description)
            VALUES (:achievement_id, :file_name, :achievement_name, :achievement_description)
            RETURNING {READ_PARAMS}
        """,
        values={
            "achievement_id": achievement_id,
            "file_name": file_name,
            "achievement_name": achievement_name,
            "achievement_description": achievement_description,
        },
    )
    assert achievement is not None
    return cast(Achievement, achievement)


async def fetch_one(achievement_id: UUID) -> Achievement | None:
    achievement = await clients.database.fetch_one(
        query=f"""
            SELECT {READ_PARAMS}
            FROM achievements
            WHERE achievement_id = :achievement_id
        """,
        values={
            "achievement_id": achievement_id,
        },
    )
    return cast(Achievement, achievement) if achievement is not None else None

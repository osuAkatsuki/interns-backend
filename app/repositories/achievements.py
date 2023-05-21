from typing import Any
from typing import cast
from typing import TypedDict

from app import clients

READ_PARAMS = """\
    achievement_id,
    file_name,
    achievement_name,
    achievement_description
"""


class Achievement(TypedDict):
    achievement_id: int
    file_name: str
    achievement_name: str
    achievement_description: str


def to_string(achievement: Achievement) -> str:
    attrs = (
        achievement["file_name"],
        achievement["achievement_name"],
        achievement["achievement_description"],
    )
    return "+".join(attrs)


async def create(
    achievement_id: int,
    file_name: str,
    achievement_name: str,
    achievement_description: str,
) -> Achievement:
    achievement = await clients.database.fetch_one(
        query=f"""
            INSERT INTO achievements (achievement_id, file_name, achievement_name, achievement_description)
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


async def fetch_one(achievement_id: int) -> Achievement | None:
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


async def fetch_many(
    page: int | None = None,
    page_size: int | None = None,
) -> list[Achievement]:
    query = f"""
        SELECT {READ_PARAMS}
        FROM achievements
    """
    values: dict[str, Any] = {}

    if page is not None and page_size is not None:
        query += f"""\
            LIMIT :limit
            OFFSET :offset
        """
        values["limit"] = page_size
        values["offset"] = (page - 1) * page_size

    achievements = await clients.database.fetch_all(query, values)
    return cast(list[Achievement], achievements)

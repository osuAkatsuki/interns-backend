from typing import Any
from typing import cast
from typing import TypedDict

from server import clients

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


async def create(
    achievement_id: int,
    file_name: str,
    achievement_name: str,
    achievement_description: str,
) -> Achievement:
    _achievement = await clients.database.fetch_one(
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
    assert _achievement is not None
    return cast(Achievement, _achievement)

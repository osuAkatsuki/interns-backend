from datetime import datetime
from typing import cast
from typing import TypedDict

from app import clients

READ_PARAMS = """\
    achievement_id,
    account_id,
    created_at
"""


class UserAchievement(TypedDict):
    achievement_id: int
    account_id: int
    created_at: datetime


async def create(
    achievement_id: int,
    account_id: int,
) -> UserAchievement:
    query = f"""\
        INSERT INTO user_achievements (achievement_id, account_id)
        VALUES (:achievement_id, :account_id)
        RETURNING {READ_PARAMS}
    """
    values = {
        "achievement_id": achievement_id,
        "account_id": account_id,
    }
    user_achievement = await clients.database.fetch_one(query, values)
    assert user_achievement is not None
    return cast(UserAchievement, user_achievement)


async def fetch_one(achievement_id: int, account_id: int) -> UserAchievement | None:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM user_achievements
        WHERE achievement_id = :achievement_id AND account_id = :account_id
    """
    values = {
        "achievement_id": achievement_id,
        "account_id": account_id,
    }
    user_achievement = await clients.database.fetch_one(query, values)
    return (
        cast(UserAchievement, user_achievement)
        if user_achievement is not None
        else None
    )


async def fetch_many(
    achievement_id: int | None = None,
    account_id: int | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> list[UserAchievement]:
    query = f"""\
        SELECT {READ_PARAMS}
        FROM user_achievements
        WHERE achievement_id = COALESCE(:achievement_id, achievement_id)
        AND account_id = COALESCE(:account_id, account_id)
    """
    values = {
        "achievement_id": achievement_id,
        "account_id": account_id,
    }
    if page is not None and page_size is not None:
        query += f"""
            LIMIT :page_size
            OFFSET :offset
        """
        values["page_size"] = page_size
        values["offset"] = (page - 1) * page_size

    user_achievements = await clients.database.fetch_all(query, values)
    return cast(list[UserAchievement], user_achievements)

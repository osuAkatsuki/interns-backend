# we use the ranked status from the osu!api
class BeatmapRankedStatus:
    GRAVEYARD = -2
    WIP = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


# there is also a ranked status from osu!direct
class BeatmapDirectRankedStatus:
    RANKED = 0
    PENDING = 2
    QUALIFIED = 3
    ALL_STATUSES = 4
    # PENDING = 5 # ??
    RANKED = 7
    LOVED = 8


# there is also a ranked status /web handlers like osu-getscores.php
class BeatmapWebRankedStatus:
    NOT_SUBMITTED = -1
    PENDING = 0
    UPDATE_AVAILABLE = 1
    RANKED = 2
    APPROVED = 3
    QUALIFIED = 4
    LOVED = 5


def to_web_status(ranked_status: int) -> int:
    match ranked_status:
        case BeatmapRankedStatus.GRAVEYARD:
            return BeatmapWebRankedStatus.PENDING
        case BeatmapRankedStatus.WIP:
            return BeatmapWebRankedStatus.PENDING
        case BeatmapRankedStatus.PENDING:
            return BeatmapWebRankedStatus.PENDING
        case BeatmapRankedStatus.RANKED:
            return BeatmapWebRankedStatus.RANKED
        case BeatmapRankedStatus.APPROVED:
            return BeatmapWebRankedStatus.APPROVED
        case BeatmapRankedStatus.QUALIFIED:
            return BeatmapWebRankedStatus.QUALIFIED
        case BeatmapRankedStatus.LOVED:
            return BeatmapWebRankedStatus.LOVED
        case _:
            raise ValueError(f"Invalid ranked status: {ranked_status}")

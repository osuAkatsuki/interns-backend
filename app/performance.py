from typing import TypedDict

from akatsuki_pp_py import Beatmap as CalculatorBeatmap
from akatsuki_pp_py import Calculator

# TODO: we can improve the typing here to avoid the optionals
# https://github.com/osuAkatsuki/interns-backend/pull/33/files#r1181634986


class DifficultyAttributes(TypedDict):
    star_rating: float
    aim_star_rating: float | None
    speed_star_rating: float | None
    flashlight_star_rating: float | None
    slider_star_rating: float | None
    speed_note_count: float | None
    ar: float | None
    od: float | None
    stamina_star_rating: float | None
    color_star_rating: float | None  # TODO: what is this? james will know
    rhythm_star_rating: float | None
    peak: float | None
    great_hit_window: float | None


class PerformanceAttributes(TypedDict):
    performance_points: float
    difficulty: DifficultyAttributes
    aim_performance_points: float
    speed_performance_points: float
    flashlight_performance_points: float
    effective_miss_count: float
    perormance_points_difficulty: float


# TODO: cache difficulty attributes?
#       they can be passed into the calculator to save time
#       and difficulty calculation is significantly slower than performance calculation
def calculate_performance(
    osu_file_contents: bytes,
    game_mode: int,
    mods: int,
    accuracy: float,
    num_300s: int,
    num_100s: int,
    num_50s: int,
    num_misses: int,
    num_gekis: int,
    num_katus: int,
    highest_combo: int,
) -> PerformanceAttributes:
    calculator_beatmap = CalculatorBeatmap(bytes=osu_file_contents)
    calculator = Calculator(
        mode=game_mode,
        mods=mods,
        acc=accuracy,
        n_geki=num_gekis,
        n_katu=num_katus,
        n300=num_300s,
        n100=num_100s,
        n50=num_50s,
        n_misses=num_misses,
        combo=highest_combo,
        # passed_objects=score["passed_objects"],
        # clock_rate=1.0,
    )
    performance = calculator.performance(calculator_beatmap)
    return {
        "performance_points": performance.pp,  # type: ignore
        "difficulty": {
            "star_rating": performance.difficulty.stars,  # type: ignore
            "aim_star_rating": performance.difficulty.aim,  # type: ignore
            "speed_star_rating": performance.difficulty.speed,  # type: ignore
            "flashlight_star_rating": performance.difficulty.flashlight,  # type: ignore
            "slider_star_rating": performance.difficulty.slider_factor,  # type: ignore
            "speed_note_count": performance.difficulty.speed_note_count,  # type: ignore
            "ar": performance.difficulty.ar,  # type: ignore
            "od": performance.difficulty.od,  # type: ignore
            "stamina_star_rating": performance.difficulty.stamina,  # type: ignore
            "color_star_rating": performance.difficulty.color,  # type: ignore
            "rhythm_star_rating": performance.difficulty.rhythm,  # type: ignore
            "peak": performance.difficulty.peak,  # type: ignore
            "great_hit_window": performance.difficulty.hit_window,  # type: ignore
        },
        "aim_performance_points": performance.pp_aim,  # type: ignore
        "speed_performance_points": performance.pp_speed,  # type: ignore
        "flashlight_performance_points": performance.pp_flashlight,  # type: ignore
        "effective_miss_count": performance.effective_miss_count,  # type: ignore
        "perormance_points_difficulty": performance.pp_difficulty,  # type: ignore
    }

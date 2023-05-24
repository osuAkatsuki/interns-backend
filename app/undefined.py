from typing import Any
from typing import TypeVar


T = TypeVar("T")


class Unset:
    def __repr__(self) -> str:
        return "Unset"

    def __copy__(self: T) -> T:
        return self

    def __reduce__(self) -> str:
        return "Unset"

    def __deepcopy__(self: T, _: Any) -> T:
        return self


UNSET = Unset()

from typing import Any, TypeVar


T = TypeVar("T")
class UndefinedType:
    def __repr__(self) -> str:
        return 'Undefined'

    def __copy__(self: T) -> T:
        return self

    def __reduce__(self) -> str:
        return 'Undefined'

    def __deepcopy__(self: T, _: Any) -> T:
        return self


Undefined = UndefinedType()
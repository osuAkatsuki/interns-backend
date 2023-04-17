import hashlib

import bcrypt


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(
        hashlib.md5(password.encode()).hexdigest().encode("utf-8"), bcrypt.gensalt()
    )


def check_password(password: str, hashword: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashword)

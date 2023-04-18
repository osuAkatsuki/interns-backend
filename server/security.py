import hashlib

import bcrypt


def hash_password(plaintext_password: str) -> bytes:
    # XXX: osu! uses md5 to hash passwords; we bcrypt on top of that.
    md5_password = hashlib.md5(plaintext_password.encode()).hexdigest()
    bcrypt_password = bcrypt.hashpw(md5_password.encode(), bcrypt.gensalt())
    return bcrypt_password


def check_password(password: str, hashword: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashword)

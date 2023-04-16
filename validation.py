import email_validator


def validate_username(username: str) -> bool:
    return 3 <= len(username) <= 16


def validate_password(password: str) -> bool:
    # Range check
    if not 8 <= len(password) <= 128:
        return False
    # Upper case char check
    if not any(char.isupper() for char in password):
        return False
    # Lower case char check
    if not any(char.islower() for char in password):
        return False
    # Number check
    if not any(char.isdigit() for char in password):
        return False

    return True


def validate_email(email: str) -> bool:
    try:
        email_validator.validate_email(email)
    except email_validator.EmailNotValidError as err:
        return False
    else:
        return True

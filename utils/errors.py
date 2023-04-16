from enum import Enum

class ServiceError(str, Enum):
    ACCOUNTS_SIGNUP_FAILED = "accounts.signup_failed"
    ACCOUNTS_NOT_FOUND = "accounts.not_found"
    ACCOUNTS_USERNAME_INVALID = "accounts.username_invalid"
    ACCOUNTS_PASSWORD_INVALID = "accounts.password_invalid"
    ACCOUNTS_EMAIL_ADDRESS_INVALID = "accounts.email_address_invalid"
    ACCOUNTS_EMAIL_ADDRESS_EXISTS = "accounts.email_address_exists"
    ACCOUNTS_USERNAME_EXISTS = "accounts.username_exists"

    SESSIONS_NOT_FOUND = "sessions.not_found"

    CREDENTIALS_NOT_FOUND = "credentials.incorrect_credentials"
    CREDENTIALS_INCORRECT = "credentials.incorrect_credentials"

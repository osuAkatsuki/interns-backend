import pytest

from server import validation


@pytest.mark.parametrize(
    "username, expected",
    [
        ("john", True),
        ("jane_doe", True),
        ("test123", True),
        ("aBcDeFg", True),
        ("user_2023", True),
        ("ab", False),  # Too short (length = 2)
        ("a", False),  # Too short (length = 1)
        ("", False),  # Empty string
        ("abcdefghijklmnopq", False),  # Too long (length = 17)
        ("thisUsernameIsWayTooLong", False),  # Too long (length = 22)
    ],
)
def test_validate_username(username, expected):
    assert validation.validate_username(username) == expected


@pytest.mark.parametrize(
    "password, expected",
    [
        ("Password123", True),
        ("q3Y1rT!78g", True),
        ("A1b2C3d4E5", True),
        ("XyZ789#_kLm", True),
        ("t2A5$7hP0", True),
        ("password", False),  # No uppercase letters or digits
        ("PASSWORD", False),  # No lowercase letters or digits
        ("12345678", False),  # No uppercase or lowercase letters
        ("Password", False),  # No digits
        ("password123", False),  # No uppercase letters
        ("PASSWORD123", False),  # No lowercase letters
        ("abcDE", False),  # Too short and no digits
        ("aA1", False),  # Too short
        ("", False),  # Empty string
        ("aA1" * 50, False),  # Too long (length = 150)
    ],
)
def test_validate_password(password, expected):
    assert validation.validate_password(password) == expected


@pytest.mark.parametrize(
    "email, expected",
    [
        ("john.doe@example.com", True),
        ("jane_doe@example.co.uk", True),
        ("test.user+123@subdomain.example.org", True),
        ("firstname.lastname@example.travel", True),
        ("test123@test.edu", True),
        ("john.doe@example", False),  # Missing TLD (top-level domain)
        ("john.doe@.com", False),  # Missing domain name
        ("john.doe@com", False),  # Missing "@" symbol and domain name
        ("john.doe@exam_ple.com", False),  # Invalid character "_" in domain name
        ("john.doe@exa(mple.com", False),  # Invalid character "(" in domain name
        ("john.doe@exa)mple.com", False),  # Invalid character ")" in domain name
        (
            "john.doe@exa%20mple.com",
            False,
        ),  # Invalid character "%20" (encoded space) in domain name
        ("john.doe@.example.com", False),  # Leading period in domain name
        ("john.doe@example..com", False),  # Consecutive periods in domain name
        ("john.doe@example.com.", False),  # Trailing period in domain name
        ("john.doe@-example.com", False),  # Leading hyphen in domain name
        ("john.doe@example-.com", False),  # Trailing hyphen in domain name
        ("john.doe@example.com/extra", False),  # Extra characters after TLD
    ],
)
def test_validate_email(email, expected):
    assert validation.validate_email(email) == expected

import pytest

from taskflow.validation import is_valid_email, require_positive_int


@pytest.mark.parametrize(
    ("email", "expected"),
    [
        ("alice@example.com", True),
        (" alice@example.com ", True),
        ("alice.example.com", False),
        ("alice@", False),
        ("@example.com", False),
        ("", False),
        (None, False),
    ],
)
def test_is_valid_email(email, expected):
    assert is_valid_email(email) is expected


def test_require_positive_int_accepts_positive_int():
    require_positive_int(3, "quantity")


def test_require_positive_int_rejects_zero():
    with pytest.raises(ValueError, match="quantity must be positive"):
        require_positive_int(0, "quantity")

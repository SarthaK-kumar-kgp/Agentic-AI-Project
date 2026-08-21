def is_valid_email(email: str) -> bool:
    if not isinstance(email, str):
        return False

    value = email.strip()
    return "@" in value


def require_positive_int(value: int, field_name: str) -> None:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer")

    if value <= 0:
        raise ValueError(f"{field_name} must be positive")

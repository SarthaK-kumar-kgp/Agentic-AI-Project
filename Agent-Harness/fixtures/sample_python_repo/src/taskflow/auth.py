from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    username: str
    password: str
    is_active: bool = True


USERS = {
    "alice": User(username="alice", password="wonderland"),
    "bob": User(username="bob", password="builder", is_active=False),
}


def normalize_username(username: str) -> str:
    """Return the canonical username used for lookups."""
    return username.strip()


def authenticate(username: str, password: str) -> bool:
    user = USERS.get(normalize_username(username))
    if user is None:
        return False
    return user.is_active and user.password == password

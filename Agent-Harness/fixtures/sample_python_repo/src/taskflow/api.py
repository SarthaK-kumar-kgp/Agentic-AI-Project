from taskflow.auth import authenticate
from taskflow.validation import is_valid_email


def login(payload: dict) -> tuple[int, dict]:
    username = payload.get("username", "")
    password = payload.get("password", "")

    if authenticate(username, password):
        return 200, {"ok": True, "message": "logged in"}

    return 401, {"ok": False, "error": "invalid credentials"}


def register(payload: dict) -> tuple[int, dict]:
    email = payload.get("email", "")
    username = payload.get("username", "")

    if not username:
        return 400, {"ok": False, "error": "username is required"}

    if not is_valid_email(email):
        return 400, {"ok": False, "error": "valid email is required"}

    return 201, {"ok": True, "username": username, "email": email}

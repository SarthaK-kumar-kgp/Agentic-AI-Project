from taskflow.api import login, register


def test_login_success_returns_200():
    status, body = login({"username": "alice", "password": "wonderland"})

    assert status == 200
    assert body["ok"] is True


def test_login_bad_password_returns_401():
    status, body = login({"username": "alice", "password": "wrong"})

    assert status == 401
    assert body == {"ok": False, "error": "invalid credentials"}


def test_register_rejects_invalid_email():
    status, body = register({"username": "charlie", "email": "charlie-at-example"})

    assert status == 400
    assert body["error"] == "valid email is required"

from taskflow.auth import authenticate, normalize_username


def test_normalize_username_trims_and_lowercases():
    assert normalize_username(" Alice ") == "alice"


def test_authenticate_accepts_case_insensitive_username():
    assert authenticate("ALICE", "wonderland") is True


def test_authenticate_rejects_inactive_user():
    assert authenticate("bob", "builder") is False

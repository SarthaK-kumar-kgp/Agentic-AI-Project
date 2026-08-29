from notekeeper.search import search_notes


def test_search_notes_is_case_insensitive():
    notes = [
        {"title": "Launch Plan", "body": "Roadmap notes"},
        {"title": "Random", "body": "nothing useful"},
    ]

    assert search_notes(notes, "launch") == [notes[0]]


def test_search_notes_ranks_title_match_before_body_match():
    notes = [
        {"title": "Daily Notes", "body": "launch launch launch"},
        {"title": "Launch Plan", "body": "short"},
    ]

    assert search_notes(notes, "launch")[0]["title"] == "Launch Plan"


def test_search_notes_returns_empty_list_when_no_match():
    notes = [{"title": "Daily Notes", "body": "standup"}]

    assert search_notes(notes, "launch") == []

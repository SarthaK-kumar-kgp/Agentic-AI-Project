from notekeeper.summary import first_sentence, summarize_note


def test_first_sentence_keeps_period():
    assert first_sentence("First sentence. Second sentence.") == "First sentence."


def test_summarize_note_adds_ellipsis_when_truncated():
    note = {
        "body": "This is a very long note summary that should be shortened for display. More text."
    }

    assert summarize_note(note, max_length=24) == "This is a very long..."

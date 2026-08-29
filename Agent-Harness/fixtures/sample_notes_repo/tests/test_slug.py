from notekeeper.slug import slugify


def test_slugify_lowercases_and_replaces_spaces():
    assert slugify("Meeting Notes") == "meeting-notes"


def test_slugify_removes_punctuation_and_collapses_dashes():
    assert slugify("  Q3: Launch Plan!!!  ") == "q3-launch-plan"


def test_slugify_handles_multiple_spaces():
    assert slugify("Project    Status") == "project-status"

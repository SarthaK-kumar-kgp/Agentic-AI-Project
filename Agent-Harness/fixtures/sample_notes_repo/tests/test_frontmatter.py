from notekeeper.frontmatter import parse_note


def test_parse_note_extracts_title_and_body():
    text = """---
title: Meeting Notes
tags: work, planning
---
Discuss launch plan.
"""

    note = parse_note(text)

    assert note["title"] == "Meeting Notes"
    assert note["body"] == "Discuss launch plan."


def test_parse_note_converts_tags_to_lowercase_list():
    text = """---
title: Meeting Notes
tags: Work, Planning
---
Discuss launch plan.
"""

    note = parse_note(text)

    assert note["tags"] == ["work", "planning"]


def test_parse_note_without_frontmatter_has_empty_metadata():
    note = parse_note("Plain body only")

    assert note == {
        "title": "",
        "tags": [],
        "body": "Plain body only",
    }

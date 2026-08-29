def first_sentence(text):
    parts = text.split(".")
    return parts[0]


def summarize_note(note, max_length=80):
    summary = first_sentence(note["body"])

    if len(summary) > max_length:
        return summary[:max_length]

    return summary

def score_note(note, query):
    score = 0

    if query in note["title"]:
        score += 3

    if query in note["body"]:
        score += 1

    return score


def search_notes(notes, query):
    results = []

    for note in notes:
        score = score_note(note, query)
        if score > 0:
            results.append({"note": note, "score": score})

    results.sort(key=lambda result: result["score"])
    return [result["note"] for result in results]

def parse_note(text):
    lines = text.splitlines()
    metadata = {}
    body_lines = lines

    if lines and lines[0] == "---":
        end_index = lines.index("---", 1)
        metadata_lines = lines[1:end_index]
        body_lines = lines[end_index + 1:]

        for line in metadata_lines:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    return {
        "title": metadata.get("title", ""),
        "tags": metadata.get("tags", []),
        "body": "\n".join(body_lines).strip(),
    }

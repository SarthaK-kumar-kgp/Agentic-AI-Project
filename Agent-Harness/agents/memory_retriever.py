import json
from pathlib import Path
from nltk.corpus import stopwords


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_FILE = PROJECT_ROOT / "memory" / "permanent_memory.json"


class MemoryRetriever:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = Path(memory_file)

    def retrieve(self, user_task, limit):
        memory_text = self.memory_file.read_text()
        memory = json.loads(memory_text)
        keywords = self.get_keywords(user_task)
        scored_memories = []

        for memory_type in ["preferences", "facts", "lessons", "metrics"]:
            items = memory.get(memory_type, [])
            for item in items:
                if isinstance(item, str):
                    text = item
                    tags = []
                    formatted_item = {
                        "type": memory_type,
                        "text": item,
                    }
                else:
                    text = item.get("text") or ""
                    tags = item.get("tags") or []
                    formatted_item = dict(item)
                    formatted_item["type"] = memory_type

                score = 0
                for keyword in keywords:
                    for tag in tags:
                        if keyword == tag.lower():
                            score = score + 3

                    if keyword in text.lower():
                        score = score + 1

                if memory_type == "preferences":
                    score = score + 1

                if score > 0:
                    scored_memories.append(
                        {
                            "score": score,
                            "memory": formatted_item,
                        }
                    )

        scored_memories.sort(key=lambda item: item["score"], reverse=True)

        results = []
        for item in scored_memories[:limit]:
            results.append(item["memory"])

        return results

    def get_keywords(self, text):
        try:
            stop_words = set(stopwords.words("english"))
        except LookupError:
            raise RuntimeError("NLTK stopwords data is missing. Run: python3 -m nltk.downloader stopwords")

        clean_text = ""
        for character in text.lower():
            if character.isalnum():
                clean_text = clean_text + character
            else:
                clean_text = clean_text + " "

        keywords = []
        for word in clean_text.split():
            if word not in stop_words and len(word) > 2:
                keywords.append(word)

        return keywords

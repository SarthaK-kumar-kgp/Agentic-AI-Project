import json
from pathlib import Path

from agents.config import MAX_FACTS, MAX_LESSONS, MAX_METRICS, MAX_PREFERENCES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY_FILE = PROJECT_ROOT / "memory" / "permanent_memory.json"

MEMORY_LIMITS = {
    "facts": MAX_FACTS,
    "lessons": MAX_LESSONS,
    "preferences": MAX_PREFERENCES,
    "metrics": MAX_METRICS,
}


class MemoryEditor:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = Path(memory_file)

    def apply_decision(self, decision, current_timestamp):
        if not isinstance(decision, dict):
            return {
                "changed": False,
                "applied": [],
                "skipped": ["Memory decision was not a JSON object."],
            }

        operations = decision.get("operations")
        if not isinstance(operations, list):
            return {
                "changed": False,
                "applied": [],
                "skipped": ["Memory decision did not contain an operations list."],
            }

        memory = json.loads(self.memory_file.read_text())
        applied = []
        skipped = []

        for operation in operations:
            if not self.is_valid_operation(operation):
                skipped.append(operation)
                continue

            action = operation["action"]
            memory_type = operation["memory_type"]

            if action == "add":
                new_item = self.create_memory_item(memory, operation, memory_type, current_timestamp)
                memory[memory_type].append(new_item)
                applied.append({"action": "add", "memory_type": memory_type, "id": new_item["id"]})

            if action == "update":
                updated = self.update_memory_item(memory, operation, current_timestamp)
                if updated:
                    applied.append(
                        {
                            "action": "update",
                            "memory_type": memory_type,
                            "id": operation["target_id"],
                        }
                    )
                else:
                    skipped.append(operation)

        self.enforce_limits(memory)

        if applied:
            self.memory_file.write_text(json.dumps(memory, indent=2))

        return {
            "changed": len(applied) > 0,
            "applied": applied,
            "skipped": skipped,
        }

    def is_valid_operation(self, operation):
        if not isinstance(operation, dict):
            return False

        action = operation.get("action")
        if action not in ["add", "update"]:
            return False

        memory_type = operation.get("memory_type")
        if memory_type not in MEMORY_LIMITS:
            return False

        text = operation.get("text")
        if not isinstance(text, str) or text.strip() == "":
            return False

        tags = operation.get("tags")
        if not isinstance(tags, list):
            return False

        if action == "update" and not operation.get("target_id"):
            return False

        return True

    def create_memory_item(self, memory, operation, memory_type, current_timestamp):
        return {
            "id": self.next_id(memory, memory_type),
            "text": operation["text"],
            "tags": operation["tags"],
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
        }

    def update_memory_item(self, memory, operation, current_timestamp):
        items = memory[operation["memory_type"]]

        for item in items:
            if item.get("id") == operation["target_id"]:
                item["text"] = operation["text"]
                item["tags"] = operation["tags"]
                item["updated_at"] = current_timestamp
                return True

        return False

    def next_id(self, memory, memory_type):
        prefix = memory_type[:-1]
        highest_number = 0

        for item in memory.get(memory_type, []):
            item_id = item.get("id", "")
            if not item_id.startswith(prefix + "-"):
                continue

            number_text = item_id.replace(prefix + "-", "")
            if number_text.isdigit() and int(number_text) > highest_number:
                highest_number = int(number_text)

        return f"{prefix}-{highest_number + 1:03d}"

    def enforce_limits(self, memory):
        for memory_type, limit in MEMORY_LIMITS.items():
            items = memory.get(memory_type, [])
            memory[memory_type] = items[-limit:]

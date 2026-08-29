# Memory

This folder stores long-term memory for the agent harness.

For now, memory uses JSON files. No vector database yet.

## Memory Types

### Temporary Memory

Temporary memory exists only during one task run.

Purpose:

- track recent observations
- keep useful task-local facts
- avoid repeated actions
- help the planner stay focused during the current run

Temporary memory should stay small and bounded.

### Permanent Memory

Permanent memory survives across task runs.

Purpose:

- remember reusable project facts
- remember user/project preferences
- remember useful lessons from previous runs
- track simple success/failure metrics

Permanent memory should not be fully sent to the LLM every time. The harness should retrieve only relevant memory for the current task.

## Permanent Memory File

Main file:

```text
memory/permanent_memory.json
```

Current structure:

```json
{
  "_schema": {
    "memory_item": {
      "id": "fact-001",
      "text": "The memory content.",
      "tags": ["python", "pytest"],
      "created_at": "2026-08-29T10:30:00",
      "updated_at": "2026-08-29T10:30:00"
    }
  },
  "facts": [],
  "lessons": [],
  "preferences": [],
  "metrics": []
}
```

Each memory item should have:

- `id`: stable unique memory id
- `text`: the actual memory
- `tags`: keywords used for retrieval
- `created_at`: when the memory was first created
- `updated_at`: when the memory was last changed

## Update Rule

Newer factual memory can replace older factual memory when both describe the same thing.

Example:

```text
python_version = 3.10
```

can replace:

```text
python_version = 3.9
```

But lessons and procedures should usually be merged or appended, not blindly overwritten.

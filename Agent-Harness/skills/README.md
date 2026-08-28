# Skills Index

This folder contains reusable skills for the agent harness.

## Available Skills

### debug-pytest-failures

- Path: `debug-pytest-failures/SKILL.md`
- Use when: The task asks the agent to debug failing pytest tests.

## Skill Entry Format

Each skill should have:

- Folder name
- Skill path, ending in `SKILL.md`
- Short description of when to use it

Example:

```md
### debug-pytest-failures

- Path: `debug-pytest-failures/SKILL.md`
- Use when: The task asks the agent to debug failing pytest tests.
```

## Selection Rule

If no listed skill clearly matches the user task, return `skill_found: false`.

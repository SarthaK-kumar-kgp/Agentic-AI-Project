# Agent Harness

This project is a small local harness for testing how an LLM agent solves coding tasks, learns from previous runs, and uses tools safely.

The main idea is simple: give the agent a broken Python repo, let it inspect files, run tests, edit code, and keep a record of what happened. Over time, the harness can also build reusable skills and memory from past runs.

## What It Does

The harness can:

- create a fresh copy of a test repository for every run
- ask an LLM planner what to do next
- run controlled tools like file listing, file reading, file writing, search, and pytest
- save each step into SQLite
- keep recent run history so the agent does not only see the last action
- load relevant skills before starting a task
- update temporary memory during a run
- update permanent memory after a run
- create a final summary when the task succeeds
- create a partial summary when max iterations are reached

Each run happens inside `runs/task_<id>/workspace`, so the original fixture repo is not directly changed.

## Project Shape

```text
agents/
  agent_loop.py          Main loop that runs the harness
  planner.py             LLM callers: planner, summarizer, skill/memory generators
  prompt.py              System prompts
  config.py              Main settings
  memory_retriever.py    Finds useful permanent memory before a run
  memory_editor.py       Updates permanent memory after a run
  skill_editor.py        Writes or updates skill files

tools/
  tools.py               Controlled local tools
  tool_registry.py       Maps tool names to tool functions

storage/
  sql_store.py           SQLite table setup and helper methods
  harness.sqlite3        Run logs

fixtures/
  sample_python_repo/    Small taskflow test repo
  sample_finance_repo/   Small finance test repo
  sample_notes_repo/     Small notes test repo

skills/
  README.md              Skill index
  */SKILL.md             Reusable skill instructions

memory/
  permanent_memory.json  Long-term memory
  readme.md              Memory design notes
```

## How A Run Works

1. A new task is created in SQLite.
2. The selected fixture repo is copied into a fresh workspace.
3. Permanent memory is searched for useful context.
4. The skills index is checked for a matching skill.
5. The planner chooses one tool action at a time.
6. The harness runs the tool and logs the result.
7. Every few iterations, temporary memory is updated.
8. If the agent finishes, a final summary is created.
9. If max iterations are reached, a partial summary is created instead.
10. Skills and permanent memory can be updated from the run.

## Setup

From the project folder:

```bash
cd /Users/sarthakkumar/Documents/Internship/Agents/Agent-Harness
```

Install the basic packages:

```bash
pip install openai python-dotenv nltk pytest
```

Download NLTK stopwords once:

```bash
python3 -m nltk.downloader stopwords
```

Create a `.env` file with your key:

```text
DEEPSEEK_API_KEY=your_key_here
```

## Choose The Test Repo

Change this value in `agents/config.py`:

```python
FIXTURE_REPO_NAME = "sample_notes_repo"
```

Available fixture repos:

- `sample_python_repo`
- `sample_finance_repo`
- `sample_notes_repo`

## Run The Harness

From `Agent-Harness`:

```bash
python3 ./agents/agent_loop.py
```

It will ask for a task:

```text
Task:
```

Example:

```text
Can you find the problem in the repository and fix the issue?
```

During the run, you will see output like:

```text
Memory retrieved: 3
Skill check: reading skills index
Skill loaded: True
Iteration 1: run_command
Iteration 2: read_file
Iteration 3: write_file
Temporary memory updated: 5 items
Final answer: ...
```

## Skills

Skills are reusable instructions saved as markdown files.

Example:

```text
skills/debug-pytest-failures/SKILL.md
```

Before a run starts, the harness reads `skills/README.md`, checks if any skill matches the task, and gives that skill to the planner.

After a run finishes, the harness can decide whether the run taught it a reusable pattern. If yes, it can create a new skill or update an existing one.

In plain English: skills are like playbooks. They tell the agent, "when you see this kind of task, follow this kind of approach."

## Memory

Memory is split into two parts:

- temporary memory
- permanent memory

Temporary memory exists only during one run. It keeps useful notes like current failing tests, changed files, and active hypotheses.

Permanent memory lives in:

```text
memory/permanent_memory.json
```

It stores longer-term facts, lessons, preferences, and simple metrics. The harness retrieves relevant memory at the start of a task and can update memory after the task finishes.

In plain English: memory is what the harness remembers across runs; skills are the step-by-step playbooks it can reuse.

## SQLite Logs

Every run is logged in:

```text
storage/harness.sqlite3
```

Useful commands:

```bash
sqlite3 storage/harness.sqlite3 "select task_id, status, goal, created_at from tasks order by task_id desc limit 10;"
```

```bash
sqlite3 storage/harness.sqlite3 "select event_type, created_at from events where task_id = 1 order by event_id;"
```

```bash
sqlite3 storage/harness.sqlite3 "select file_name, created_at from file_changes where task_id = 1;"
```

Replace `1` with the task id you want to inspect.

## Current Status

This is a working prototype. It can solve small local Python repos, use skills, keep memory, and produce useful logs.

It is not production-grade yet. The main things still worth improving are:

- stronger loop-breaking when the agent repeats bad edits
- better duplicate detection for memory and skills
- more tests for the harness itself
- cleaner command-line options
- better tools for browsing SQLite logs

## Notes

The fixture repos are intentionally small. That is useful because it lets you clearly see how the harness behaves: what the agent reads, what it changes, when it gets stuck, and what it learns from the run.

That is the point of this project: not just whether the agent fixes code, but whether the harness helps you understand and improve the way the agent works.

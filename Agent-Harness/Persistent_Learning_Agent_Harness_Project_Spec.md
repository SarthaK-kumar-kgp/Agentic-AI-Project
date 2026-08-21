# Persistent Learning Agent Harness

## 0. Project at a Glance

We are building **one general-purpose agent harness** and making it deeper over four versions.

The harness takes a task such as:

> "Analyze this repository, find why the tests are failing, fix the problem, and verify the fix."

and gives an LLM the machinery needed to do real multi-step work.

The model is not the whole agent. The harness provides the surrounding system:

```text
                    USER TASK
                        |
                        v
                +----------------+
                |    HARNESS     |
                |                |
                | Agent Loop     |
                | Context        |
                | Tools          |
                | State          |
                | Memory         |
                | Skills         |
                | Checkpoints    |
                | Recovery       |
                | Permissions    |
                | Evaluation     |
                | Streaming      |
                +-------+--------+
                        |
                        v
                       LLM
                        |
                        v
                      Action
                        |
                        v
                       Tool
                        |
                        v
                     Result
                        |
                        +-------> back to harness
```

The finished system should feel like:

> **A small, persistent operating environment for an AI worker.**

It is **not** another business application like the Decision Intelligence System we already built. This time, we are building the **infrastructure underneath an agent**.

---

# 1. Why This Project

The previous project taught us:

- multi-agent coordination
- persistence
- streaming
- shared state
- disagreement and re-evaluation

The next natural step is to move one layer deeper.

Instead of asking:

> "How can multiple agents solve a business problem?"

we ask:

> **"What does an agent need around it to reliably perform work over time?"**

This project is designed to answer that question.

---

# 2. The Core Mental Model

A useful progression is:

```text
LLM
  |
  +-- generates text
```

Then:

```text
Agent
  |
  +-- LLM
  +-- loop
  +-- tools
  +-- observations
```

Then:

```text
Harness
  |
  +-- agent loop
  +-- tools
  +-- context
  +-- state
  +-- memory
  +-- skills
  +-- permissions
  +-- checkpointing
  +-- recovery
  +-- streaming
  +-- evaluation
```

The model is the **brain**.

The harness is the **environment, memory, control system, and safety system around the brain**.

---

# 3. Final Goal

At the end of Version 4, the harness should be able to do something like:

```text
User:
Analyze this Python repository, identify the failing tests,
fix the root cause, and verify the fix.
```

The system should:

1. Create a persistent task.
2. Start the agent loop.
3. Give the model access to safe tools.
4. Let the agent inspect the repository.
5. Let the agent run tests.
6. Let the agent observe failures.
7. Let the agent change files.
8. Let the agent run tests again.
9. Retrieve useful previous memories or skills.
10. Save progress regularly.
11. Recover if a tool or process fails.
12. Ask the user for approval when necessary.
13. Stream important events to the UI.
14. Finish with a complete execution history.
15. Allow the run to be replayed and evaluated.

The final system is therefore not just:

```text
Prompt -> LLM -> Answer
```

It is:

```text
Goal
  |
  v
Plan / decide
  |
  v
Act
  |
  v
Observe
  |
  v
Remember
  |
  v
Learn
  |
  v
Recover if necessary
  |
  v
Continue
  |
  +--------------------+
                       |
                    until done
```

---

# 4. Hard Constraints

## 4.1 Timeline

Target:

**12–14 days total**

Do not turn this into a 1–2 month project. If a feature is too large, cut the feature.

## 4.2 Paid services

The only paid dependency should be:

**LLM API usage.**

Everything else should run locally or be open-source/free.

We do not need:

- AWS
- GCP
- Azure
- managed databases
- managed Redis
- Pinecone
- Supabase
- managed Kafka
- paid observability platforms
- paid evaluation platforms

SQLite is especially suitable because it is local, serverless, zero-configuration, and stored on disk. citeturn915813search0turn915813search1turn915813search5

## 4.3 Frontend

Do not spend time learning frontend development.

Use **Claude to build the frontend**.

Your focus is the harness/backend architecture.

The frontend only needs to display:

- current task
- agent activity
- tool calls
- important state changes
- memory/skill retrieval
- checkpoints
- failures/retries
- final result
- run history

FastAPI supports WebSockets and streaming-style communication, so it is a good local backend choice. citeturn915813search2turn915813search4

---

# 5. What the Project Is NOT

To keep scope under control:

- It is not a Claude Code clone.
- It is not a full coding-agent product.
- It is not a multi-agent swarm.
- It is not a distributed system.
- It is not an MCP implementation.
- It is not a cloud platform.
- It is not a model-training project.
- It is not a research project about making LLMs smarter.
- It is not a vector-database project.
- It is not a benchmark paper.

The objective is:

> **Understand and build the important pieces that make an agent reliable.**

---

# 6. One Concrete Environment for All Versions

Do not change the application every version.

Use one small, controlled local environment: a small Python repository containing source files, tests, a few intentional bugs, recurring tasks, and tasks where previous experience can help.

Example tasks:

```text
Task A:
Find why tests/auth_test.py fails.

Task B:
Fix the authentication bug.

Task C:
Add a missing validation rule.

Task D:
Find why the API returns the wrong status code.

Task E:
Run the full test suite and explain failures.
```

This environment gives the agent something real to interact with while keeping the problem small.

---

# 7. Version 1 — Build the Basic Agent Harness

## Question V1 Answers

> **"What does an LLM need around it to actually behave like an agent?"**

## V1 Goal

Build the smallest useful agent runtime.

The agent should:

1. receive a task
2. decide the next action
3. call a tool
4. observe the result
5. decide what to do next
6. continue until the task is complete

## V1 Architecture

```text
                    USER
                      |
                      v
                 Task Manager
                      |
                      v
                 Agent Loop
                      |
             +--------+--------+
             |                 |
             v                 v
          Context           Tools
             |                 |
             +--------+--------+
                      |
                      v
                     LLM
                      |
                      v
                   Action
                      |
                      v
                    Tool
                      |
                      v
                  Result
                      |
                      +-------> Agent Loop
```

## V1 Tools

Start with about five:

```text
read_file()
write_file()
search()
run_command()
list_files()
```

The point is to understand the tool interface, not to build a giant tool library.

Every tool should have:

```text
Name
Description
Input
Output
Errors
```

## V1 Context

The agent should know:

- current goal
- current task state
- previous important actions
- latest observation
- available tools
- relevant constraints

Do not build sophisticated memory yet.

## V1 Persistence

Store the current task state, for example:

```text
Task ID: 42

Goal:
Find why the tests are failing.

Status:
RUNNING

Last action:
run_tests()

Last observation:
3 tests failed.
```

If the process restarts, the task should still exist.

## V1 Streaming

Stream meaningful events such as:

```text
TASK_STARTED
AGENT_STARTED
TOOL_CALLED
TOOL_COMPLETED
AGENT_STEP_COMPLETED
TOOL_FAILED
TASK_COMPLETED
```

Do not make token streaming the main goal. The interesting thing is streaming **what the agent is doing**.

## V1 Success Criteria

V1 is finished when:

- the agent can perform a multi-step task
- the agent can use tools
- tool results influence later actions
- task state survives restart
- the UI shows live activity
- failures do not immediately destroy the entire task

---

# 8. Version 2 — Memory and Skills

## Question V2 Answers

> **"Can the agent learn something useful from previous work and reuse it later?"**

Now we extend the SAME harness.

## V2 Goal

Introduce two ideas:

### Memory
Persistent information that may be useful later.

### Skills
Reusable procedures that help the agent solve recurring tasks.

---

# 9. Memory

Do not think:

> Memory = previous conversation.

Instead think:

> Memory = information worth keeping after the task is over.

A useful first design:

```text
Task Memory
    |
    +-- what happened in this task

Knowledge Memory
    |
    +-- stable facts

Experience Memory
    |
    +-- what worked
    +-- what failed
    +-- useful lessons
```

Example:

Task 1:

```text
Fix authentication failure.
```

The agent discovers:

```text
DATABASE_URL was missing.
```

The harness stores that experience.

Task 2 arrives:

```text
Fix another authentication failure.
```

The harness retrieves the previous experience so the agent can investigate the right possibility earlier.

## Memory Retrieval

Start simple.

Use:

- task type
- keywords
- tags
- project
- recency
- simple text matching

Only introduce embeddings later if simple retrieval becomes inadequate.

The important question is:

> **When should memory be saved, and when should it be retrieved?**

---

# 10. Skills

Skills are reusable ways of performing a task.

Example:

The agent repeatedly deploys a Python service and discovers:

```text
1. Check dependencies.
2. Check environment variables.
3. Build.
4. Start.
5. Run health check.
```

The harness can store:

```text
Skill:
Python Service Deployment
```

Next time:

```text
New task
   |
   v
Search skills
   |
   v
Python Deployment Skill
   |
   v
Agent adapts procedure to current situation
```

This is more powerful than remembering a sentence: it remembers **how to perform something**.

## V2 Architecture

```text
                         TASK
                           |
                           v
                      AGENT LOOP
                           |
              +------------+------------+
              |                         |
              v                         v
           MEMORY                    SKILLS
              |                         |
              +------------+------------+
                           |
                           v
                          LLM
                           |
                           v
                         TOOL
                           |
                           v
                        RESULT
                           |
                  +--------+--------+
                  |                 |
                  v                 v
               Remember         Improve skill
```

## V2 Success Criteria

V2 is finished when:

- useful past information can be retrieved
- memory persists across sessions
- memory can influence decisions
- recurring procedures can become skills
- skills can be reused
- temporary task state is separated from longer-lived memory

---

# 11. Version 3 — Evaluation, Trajectories, and Replay

## Question V3 Answers

> **"How do I know whether the agent is actually getting better?"**

Until V3, we mostly observe the agent. Now we start measuring it.

## Every Run Becomes a Trajectory

For each task, record:

```text
Run ID
Task
Step 1: action, tool, result
Step 2: action, tool, result
Step 3: ...
Final result
Success / failure
```

Example:

```text
Run #184

Task:
Find why tests are failing.

Step 1:
search("auth")

Step 2:
read_file("auth.py")

Step 3:
run_command("pytest")

Step 4:
write_file("auth.py")

Step 5:
run_command("pytest")

Result:
SUCCESS
```

## Evaluation

Create around 20–50 carefully designed local tasks.

Measure things like:

```text
Success rate
Average steps
Average retries
Tool failures
Time
Token usage
```

Compare:

```text
Agent without memory
vs.
Agent with memory
vs.
Agent with memory + skills
```

Now you can answer:

> "Did memory actually help?"

instead of assuming it helped.

## Replay

Take an old run and replay it under different configurations:

```text
Run #184
     |
     +---- Memory OFF
     |
     +---- Memory ON
     |
     +---- Skills OFF
     |
     +---- Skills ON
```

This turns the harness into a small **agent laboratory**.

## V3 Success Criteria

V3 is finished when:

- every run has a trajectory
- runs can be inspected
- failures can be analyzed
- the same task can be run with different configurations
- the system reports basic metrics
- old runs can be replayed

---

# 12. Version 4 — Reliability and Long-Running Work

## Question V4 Answers

> **"Can the harness keep an agent working even when things go wrong?"**

This is where the system becomes a serious harness.

## Checkpointing

During a long task:

```text
Task
 |
 +-- Step 1 completed
 |
 +-- Step 2 completed
 |
 +-- Checkpoint
 |
 +-- Step 3 completed
 |
 +-- Checkpoint
 |
 +-- Step 4 ...
```

If the process dies:

```text
Restart
   |
   v
Load latest checkpoint
   |
   v
Continue from there
```

## Failure Recovery

Introduce intentional failures:

- tool timeout
- tool returns invalid output
- LLM request fails
- process crashes
- unexpected exception
- command exits with error

The harness should decide whether to retry, recover, ask the agent to reconsider, ask the human, or stop.

## Human Approval

Potentially destructive actions should require approval.

Example:

```text
Agent wants to delete a file.

Harness:
This action is potentially destructive.
Approve?

[Yes] [No]
```

The agent pauses. The harness remembers the pending operation. When the user approves, the task resumes.

## Permissions

Example levels:

```text
LOW RISK
read_file
search
list_files

MEDIUM RISK
write_file
run_tests

HIGH RISK
delete_file
git_reset
external network calls
```

The harness can decide whether an action runs automatically, requires confirmation, or is blocked.

---

# 13. Event Model

A simple event history should exist across the entire project.

Examples:

```text
TaskCreated
AgentStarted

ToolCalled
ToolCompleted
ToolFailed

MemoryRetrieved
MemoryCreated

SkillRetrieved
SkillCreated
SkillUpdated

CheckpointCreated

ApprovalRequested
ApprovalGranted
ApprovalDenied

AgentRecovered

TaskCompleted
TaskFailed
```

Think of this as the system's permanent activity log.

It answers:

> "What actually happened?"

---

# 14. What You Should Study Before Starting

You do **not** need to study every modern agent framework.

Study the underlying ideas first.

## A. Agent Loop

Understand:

```text
Goal
  |
Think
  |
Act
  |
Observe
  |
Think again
  |
...
```

Learn:

- tool calling
- observations
- stopping conditions
- iterative execution
- failure handling

This is the single most important concept.

## B. Tool Calling

Understand:

- what a tool is
- how tools are described
- structured inputs
- structured outputs
- tool errors
- tool permissions

Be comfortable with JSON-style schemas.

## C. State

Understand the difference between **current state** and **history**.

Example:

```text
Current state:
Task is RUNNING.
Last step was pytest.

History:
Everything that happened before.
```

## D. Event-Driven Thinking

Understand:

> An event is something that happened.

Examples:

```text
ToolCalled
ToolCompleted
ToolFailed
MemoryCreated
CheckpointCreated
```

Learn how state can be updated from events. You do not need Kafka; you need the mental model.

## E. Persistence

Understand:

- database vs in-memory state
- transactions
- durability
- checkpoints
- restart/resume
- event history

SQLite is ideal here because it is local and requires no database server. citeturn915813search0turn915813search5

## F. Async Programming

Understand basic Python:

```text
async
await
tasks
concurrency
timeouts
cancellation
```

## G. Streaming

Understand the difference between:

```text
Request -> wait -> response
```

and:

```text
Request
  |
  +-- event
  +-- event
  +-- event
  +-- event
  |
  +-- final result
```

For this project, understand WebSockets and Server-Sent Events conceptually. FastAPI supports WebSockets directly. citeturn915813search2

## H. Memory Design

Understand the difference between:

```text
Conversation history
Task state
Long-term memory
Experience
Skills
```

The key question is:

> **What information is worth remembering?**

## I. Checkpointing

Understand:

> Save enough state so a long-running task can resume after interruption.

Study:

- checkpoint
- resume
- idempotency
- retry
- partial completion

## J. Evaluation

Learn to think in terms of:

```text
Input
Trajectory
Outcome
Metric
```

Instead of:

> "The answer looked good."

Aim for:

> "The agent succeeded on 41/50 tasks, averaged 8.2 steps, and memory reduced retries by 18%."

## K. Human-in-the-Loop

Understand:

```text
Agent wants action
        |
        v
Is action safe?
   /          \
 yes           no
 |             |
execute      request approval
```

---

# 15. Tech Stack

Keep the stack intentionally boring. That is good for this project.

| Layer | Choice | Why |
|---|---|---|
| Language | Python | Main implementation language |
| Backend | FastAPI | API + local server + WebSockets |
| Database | SQLite | Persistent local state, events, memory, skills |
| Data models | Pydantic | Clear validated boundaries between components |
| LLM | Your chosen LLM API | Only paid component |
| Frontend | Claude-generated local UI | You do not spend time learning frontend |
| Streaming | FastAPI WebSockets / SSE | Live events without extra infrastructure |
| Memory | SQLite + simple retrieval | Easy to understand and enough for the first versions |
| Skills | SQLite + structured records | Simple and persistent |
| Tests | pytest | Test the harness itself |
| Version control | Git | Version the four stages |

FastAPI's official documentation supports WebSockets and event/streaming patterns. citeturn915813search2turn915813search4

SQLite is a single-file, serverless, transactional database with no separate server process, making it a strong fit for a local two-week build. citeturn915813search1turn915813search5

---

# 16. Is LangGraph Needed?

## No — not initially.

LangGraph is explicitly designed for long-running, stateful agents and includes infrastructure for persistence, durable execution, streaming, human-in-the-loop workflows, and memory. citeturn915813search3

That sounds perfect for this project, but it is exactly why we should **not make it a dependency at the start**.

Our goal is to understand those mechanisms, not merely use them.

If LangGraph handles your:

```text
checkpointing
state transitions
persistence
streaming
recovery
```

then you may finish the project without really understanding how they work.

## Better approach

Build the first version yourself:

```text
V1
Build the loop yourself.

V2
Build memory/skills yourself.

V3
Build evaluation/replay yourself.

V4
Build checkpoint/recovery yourself.
```

After V4, study LangGraph and compare:

```text
Your implementation
        vs
LangGraph
```

Then you can see which problems LangGraph solves and why its abstractions exist.

LangGraph can become a **post-project comparison or optional extension**, not a prerequisite.

---

# 17. 12–14 Day Build Plan

## Days 1–2 — Study + Skeleton

Study:

- agent loop
- tool calling
- async Python
- state
- events
- SQLite

Build:

```text
project structure
LLM interface
Task model
Tool interface
```

## Days 3–5 — V1 Agent

Implement:

```text
agent loop
tools
context
persistent task
basic streaming
```

Demo:

> Agent reads repository -> runs tests -> investigates -> answers.

## Days 6–8 — V2 Memory + Skills

Implement:

```text
memory storage
memory retrieval
experience records
skill records
skill retrieval
```

Demo:

> Agent remembers a previous solution and reuses it.

## Days 9–10 — V3 Evaluation

Implement:

```text
trajectory recording
metrics
run history
comparison
replay
```

Demo:

> Same task with memory OFF vs ON.

## Days 11–13 — V4 Reliability

Implement:

```text
checkpoints
retry
recovery
pause/resume
human approval
permissions
```

Demo:

> Kill the agent halfway through -> restart -> agent resumes.

## Day 14 — Polish

Create:

```text
clean dashboard
architecture diagram
documentation
demo script
evaluation results
```

Git tags:

```text
v1-basic-harness
v2-memory-skills
v3-evaluation
v4-reliable-agent
```

---

# 18. Final Demonstration

The best demo is one continuous story.

Start with:

> "Here is a broken repository."

Then show:

```text
Agent starts.

Reads files.

Runs tests.

Finds failure.

Uses a tool.

Makes a change.

Runs tests again.
```

Then **kill the process**.

Restart:

```text
Loading checkpoint...

Resuming task...
```

Let it continue.

Then run the same kind of task again and show:

```text
Previous experience retrieved.
Skill retrieved.
Agent reuses what it learned.
```

Finally show evaluation:

```text
Run #1
11 steps
3 retries

Run #2
7 steps
1 retry
```

The conclusion becomes:

> **"The harness remembered experience, reused a skill, survived interruption, and let us measure how that changed behavior."**

---

# 19. What You Should Be Able to Explain After This

At the end, you should be comfortable explaining:

### Agent
What is the loop?

### Tool
How does the model interact with the outside world?

### Context
What information does the agent see at each step?

### State
What is the current state of a task?

### Memory
What information survives after the task?

### Skills
What procedures can be reused?

### Events
What actually happened?

### Checkpoints
Where can we safely resume?

### Recovery
What happens when something breaks?

### Permissions
What is the agent allowed to do?

### Evaluation
How do we know the agent is improving?

### Harness
How do all of these pieces work together to make an LLM a reliable worker?

If you can explain all of that **and show it working**, you have achieved the purpose of the project.

# Persistence Contract

This document defines what the system must preserve so a run can be inspected, stopped, and resumed later without guessing.

## Goal

Persistence here means:

- keep a durable record of what happened in a run
- keep enough state to continue the run later
- avoid rerunning nodes blindly after restart
- preserve the decision history for audit and debugging

## Current Storage

The project already stores:

- `runs`: one row per run
- `run_events`: append-only node input/output history

That is useful, but it is not yet a full resume system unless we can rebuild the active state from it.

## What Must Persist

These values are required for replay or resume:

- `run_id`
- `user_question`
- `status`
- `current_node`
- `current_iteration`
- `graph_version`
- `final_output_json`
- node inputs
- node outputs
- error payloads
- retry counters
- selected agents
- feedback decisions
- any derived state that later nodes depend on

## What Is Optional

These values are useful, but not always required for resume:

- parent event links
- timestamps
- sequence numbers
- checkpoint IDs
- visualization artifacts

## What Should Not Be Persisted

Do not store values that:

- can be safely recomputed from saved state
- are only temporary inside one node
- do not affect branching or output

Examples:

- local formatting strings
- prompt assembly helpers
- scratch variables used only inside one function

## Resume Rule

If a value can change the next node, it must be recoverable.

If losing a value would force the run to start over, it must be persisted.

If a value only helps readability, it may stay transient.

## Run Lifecycle

A run should move through these states:

- `running`
- `paused`
- `completed`
- `failed`

## Persistence Contract For Nodes

Each node must follow this rule:

1. record the input state it received
2. record the output it produced
3. record any failure if it happens
4. make outputs stable enough to reconstruct later state

## Required Resume Invariant

If a run is resumed later, the system should be able to answer:

- what node ran last
- what that node produced
- what state the graph had after that node
- what node should run next

## Phase 1 Decision

For this project, persistence will be based on two layers:

1. event history in SQLite
2. reconstructed graph state from that history

That means `run_events` is not just a log. It is the source used to rebuild the live state.

For execution, `run_id` is the durable LangGraph `thread_id`.

## Open Questions For Phase 2

- Should a resume restart from the last successful node or from the exact interrupted node?
- Should partial outputs be written before or after node completion?
- Do we want a separate checkpoint table, or is `run_events` enough for the first version?
- Should old runs be compatible across `graph_version` changes?

## Replay Mapping

This is the rulebook for rebuilding `GraphState` from `run_events`.

### Core Rule

- read events in `sequence_no` order
- only apply successful `output` events for state reconstruction
- merge each event's `output_json` into the reconstructed state
- use `runs.current_node` as the last known control position
- use `runs.status` to decide whether the run is resumable

### Node To State Mapping

| Node | Saved Output Keys | Restored State Fields | Why It Matters |
|---|---|---|---|
| `enrich_question` | `question_list` | `state["question_list"]` | needed by follow-up question node |
| `ask_follow_up_questions` | `enriched_context` | `state["enriched_context"]` | needed by planner |
| `planner_node` | `planner` | `state["planner"]` | needed by router |
| `router_node` | `router` | `state["router"]` | needed by dispatcher and specialist routing |
| `dispatcher_node` | `dispatcher` | `state["dispatcher"]` | needed to know selected agents |
| `cost_analysis_node` | `cost_agent` | `state["cost_agent"]` | needed by skeptic and decision agent |
| `performance_analysis_node` | `performance_agent` | `state["performance_agent"]` | needed by skeptic and decision agent |
| `security_analysis_node` | `security_agent` | `state["security_agent"]` | needed by skeptic and decision agent |
| `engineering_analysis_node` | `engineering_agent` | `state["engineering_agent"]` | needed by skeptic and decision agent |
| `specialist_review_gate` | `specialist_review_ready` | `state["specialist_review_ready"]` | controls whether skeptic runs |
| `skeptic_node` | `skeptic` | `state["skeptic"]` | needed by feedback agent |
| `feedback_agent` | `feedback`, `retry_round`, `specialist_review_ready`, rerun agent keys set to `None` | `state["feedback"]`, `state["retry_round"]`, `state["specialist_review_ready"]`, plus agent reset state | controls reruns and loop behavior |
| `decision_node` | `final_specialist_outputs`, `decision` | `state["final_specialist_outputs"]`, `state["decision"]` | final output for the run |

### Merge Rule

When rebuilding state:

- if output contains a key, write it into the state
- if output sets a specialist key to `None`, treat that as a reset for rerun
- do not delete unrelated fields
- keep the latest value for each field

### Control State Mapping

The following fields must also be recoverable:

- `run_id`
- `db_path`
- `user_question`
- `agent_registry`
- `retry_round`
- `dispatcher`
- `specialist_review_ready`
- `current_node`
- `current_iteration`

### Verification Checklist

Phase 2 is only complete if all of these are true:

- each node writes both input and output logs
- successful outputs contain the fields listed in the mapping table
- failed nodes write an error event
- `runs.current_node` reflects the latest node start
- `runs.status` reflects running, paused, completed, or failed
- replaying events in order reconstructs a valid `GraphState`

### Current Gaps In Code

No blocking gaps remain in the current persistence path.

One cleanup item remains: `resume_run_to_completion(...)` is still in the codebase as a fallback helper, but it is no longer used by the live resume path.

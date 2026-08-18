# Persistence Notes

## Issue:
We needed runs to stop and resume without guessing where they left off.

## Though process:
The SQLite logs already stored most of the history, but that alone was not enough. The important decision was to make `run_id` the durable LangGraph `thread_id`, then let the compiled graph resume from the checkpoint while SQLite keeps the audit trail.

## Solution:
- Kept `runs` and `run_events` as the persistence history.
- Added a SQLite checkpoint table for LangGraph state.
- Resumed with the same compiled graph instead of a separate manual runner.
- Added node-start prints so the current node and iteration are visible when a run stops or resumes.

## Issue:
`current_iteration` was being written as `0` all the time, so reruns looked the same as the first pass.

## Though process:
That made the logs hard to read and the replay story messy. We only needed one reliable iteration counter, so we reused the graph state and mirrored it into the run row and events.

## Solution:
- Tracked `current_iteration` from state instead of hardcoding `0`.
- Wrote the same iteration into run updates and event logs.
- Advanced the iteration when feedback triggers a rerun.

## Issue:
Crashes could leave a run looking active even though execution had already died.

## Though process:
That is misleading during debugging and makes resume behavior harder to trust. A failed run should say failed, not sit there as if it is still running.

## Solution:
- Wrapped `graph.invoke(...)` in a failure path.
- Logged the error into the run history.
- Marked the run as failed instead of leaving it stuck in `running`.

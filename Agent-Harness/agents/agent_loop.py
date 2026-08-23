import sys
from pathlib import Path
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from agents.config import MAX_ITERATION_NUMBER, RECENT_HISTORY_LIMIT

from agents.planner import RealPlanner, Summarizer
from storage.sql_store import SQLStore
from tools.tool_registry import run_tools


TEMPLATE_REPO = PROJECT_ROOT / "fixtures" / "sample_python_repo"
RUNS_DIR = PROJECT_ROOT / "runs"


def create_workspace(task_id):
    workspace_path = RUNS_DIR / f"task_{task_id}" / "workspace"
    shutil.copytree(
        TEMPLATE_REPO,
        workspace_path,
        ignore=shutil.ignore_patterns(".pytest_cache", "__pycache__", "*.pyc"),
    )
    return workspace_path


def extract_test_summary(observation):
    output = observation.get("output") or {}
    stdout = output.get("stdout", "")
    lines = stdout.splitlines()
    if not lines:
        return ""
    return lines[-1]


def build_action_summary(history):
    actions = []
    test_runs = []

    for item in history:
        action = {
            "iteration": item["iteration"],
            "tool_name": item["tool_name"],
            "tool_input": item["tool_input"],
            "success": item["observation"].get("success"),
        }
        actions.append(action)

        if item["tool_name"] == "run_command":
            test_runs.append(
                {
                    "iteration": item["iteration"],
                    "success": item["observation"].get("success"),
                    "summary": extract_test_summary(item["observation"]),
                }
            )

    return actions, test_runs


def get_file_changes_for_summary(store, task_id):
    rows = store.read_query(
        """
        SELECT file_name, file_difference
        FROM file_changes
        WHERE task_id = ?
        ORDER BY file_change_id
        """,
        (task_id,),
    )

    file_changes = []
    for file_name, file_difference in rows:
        file_changes.append(
            {
                "file_name": file_name,
                "file_difference": file_difference,
            }
        )
    return file_changes


def build_summary_payload(goal, history, file_changes, planner_final_answer):
    actions, test_runs = build_action_summary(history)
    return {
        "goal": goal,
        "actions": actions,
        "file_changes": file_changes,
        "test_runs": test_runs,
        "planner_final_answer": planner_final_answer,
    }


def run_agent_loop(goal="Find why the tests are failing.", max_iterations=MAX_ITERATION_NUMBER):
    planner = RealPlanner()
    summarizer = Summarizer()
    store = SQLStore()
    task_id = store.create_task(goal, status="RUNNING")
    workspace_path = create_workspace(task_id)
    latest_observation = None
    history = []

    store.create_event(
        task_id,
        "TASK_STARTED",
        {"goal": goal, "workspace_path": str(workspace_path)},
    )
    store.create_event(task_id, "AGENT_STARTED", {"agent_id": "real-planner"})

    for iteration_number in range(1, max_iterations + 1):
        recent_history = history[-RECENT_HISTORY_LIMIT:]
        action = planner.decide(iteration_number,goal, latest_observation,recent_history)
        tool_name = action["tool_name"]
        tool_input = action["tool_input"]
        explanation = action.get("explanation", "")
        step_id = store.create_step(
            task_id,
            iteration_number,
            "real-planner",
            explanation or f"Planner selected {tool_name}",
        )
        store.create_event(
            task_id,
            "PLANNER_DECISION",
            {
                "iteration_number": iteration_number,
                "action": action,
                "explanation": explanation,
            },
        )

        print(f"Iteration {iteration_number}: {tool_name}")

        if tool_name == "finish":
            planner_final_answer = tool_input["final_answer"]
            file_changes = get_file_changes_for_summary(store, task_id)
            summary_payload = build_summary_payload(
                goal,
                history,
                file_changes,
                planner_final_answer,
            )
            summary = summarizer.summarize(summary_payload)
            final_answer = summary["final_answer"]
            store.create_event(
                task_id,
                "SUMMARY_CREATED",
                {"summary": summary, "summary_payload": summary_payload},
            )
            store.create_event(task_id, "TASK_COMPLETED", {"final_answer": final_answer})
            store.update_task_status(task_id, "COMPLETED", final_answer)
            print(f"Final answer: {final_answer}")
            return {
                "task_id": task_id,
                "status": "COMPLETED",
                "final_answer": final_answer,
            }

        store.create_event(
            task_id,
            "TOOL_CALLED",
            {"tool_name": tool_name, "tool_input": tool_input},
        )
        latest_observation = run_tools(tool_name, tool_input, workspace_path=str(workspace_path))
        tool_error = latest_observation.get("error")
        if not latest_observation.get("success") and tool_error is None:
            tool_error = latest_observation.get("output")

        tool_call_id = store.create_tool_call(
            task_id,
            step_id,
            tool_name,
            tool_input,
            latest_observation.get("output"),
            tool_error,
            1 if latest_observation.get("success") else 0,
        )

        if latest_observation.get("success"):
            store.create_event(task_id, "TOOL_COMPLETED", {"tool_name": tool_name})
        else:
            store.create_event(
                task_id,
                "TOOL_FAILED",
                {"tool_name": tool_name, "error": tool_error},
            )

        if tool_name == "write_file" and latest_observation.get("success"):
            file_change = latest_observation["output"]
            store.create_file_change(
                task_id,
                tool_call_id,
                file_change["file_name"],
                file_change["file_start_text"],
                file_change["file_end_text"],
                file_change["file_difference"],
            )

        store.create_event(
            task_id,
            "AGENT_STEP_COMPLETED",
            {"iteration_number": iteration_number, "tool_name": tool_name},
        )
        history.append(
            {
                "iteration": iteration_number,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "observation": latest_observation,
            }
        )
        # print(latest_observation)

    final_answer = "Agent loop reached max_iterations."
    store.create_event(task_id, "TASK_FAILED", {"reason": final_answer})
    store.update_task_status(task_id, "FAILED", final_answer)
    return {
        "task_id": task_id,
        "status": "FAILED",
        "final_answer": final_answer,
    }


if __name__ == "__main__":
    run_agent_loop()

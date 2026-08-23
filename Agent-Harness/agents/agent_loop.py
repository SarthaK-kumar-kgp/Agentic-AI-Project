import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from agents.config import MAX_ITERATION_NUMBER, RECENT_HISTORY_LIMIT

from agents.planner import RealPlanner
from storage.sql_store import SQLStore
from tools.tool_registry import run_tools


def run_agent_loop(goal="Find why the tests are failing.", max_iterations=MAX_ITERATION_NUMBER):
    planner = RealPlanner()
    store = SQLStore()
    task_id = store.create_task(goal, status="RUNNING")
    latest_observation = None
    history = []

    store.create_event(task_id, "TASK_STARTED", {"goal": goal})
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
            final_answer = tool_input["final_answer"]
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
        latest_observation = run_tools(tool_name, tool_input)
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

"""Run the prompts from unit_test.json through the security orchestrator.

Run from this directory with:
    python run_security_tests.py
"""

import json
import time
from pathlib import Path

from security_orchestrator import input_orchestrator


TEST_FILE = Path(__file__).with_name("unit_test.json")


def load_test_cases():
    """Load category/prompt pairs directly from unit_test.json."""
    with TEST_FILE.open(encoding="utf-8") as file:
        test_groups = json.load(file)

    if not isinstance(test_groups, dict):
        raise ValueError("unit_test.json must contain an object of test categories")

    for category, prompts in test_groups.items():
        if not isinstance(prompts, list):
            raise ValueError(f"Test category '{category}' must contain a list")
        for prompt in prompts:
            if not isinstance(prompt, str):
                raise ValueError(f"Every prompt in '{category}' must be a string")
            yield category, prompt


def decision_from_result(result):
    """Return a readable decision for dict, string, None, or unexpected results."""
    if isinstance(result, dict):
        decision = str(result.get("decision", "UNKNOWN")).strip()
        return decision.split("|", 1)[0].strip(), result.get("reason", "")

    if isinstance(result, str):
        if not result.strip():
            return "EMPTY", ""
        return result.split("|", 1)[0].strip(), result

    if result is None:
        return "NO_RESULT", "The orchestrator returned None"

    return "UNKNOWN", repr(result)


def main():
    results = []
    test_cases = list(load_test_cases())
    print(f"Running {len(test_cases)} prompts from {TEST_FILE.name}...\n")

    for number, (category, prompt) in enumerate(test_cases, start=1):
        started = time.perf_counter()
        try:
            raw_result = input_orchestrator(prompt)
            elapsed_ms = (time.perf_counter() - started) * 1000
            decision, reason = decision_from_result(raw_result)
            results.append((decision, elapsed_ms))

            print(f"[{number}/{len(test_cases)}] {category}")
            print(f"    prompt:   {prompt or '<empty>'}")
            print(f"    decision: {decision}")
            print(f"    reason:   {reason or '<none>'}")
            print(f"    latency:  {elapsed_ms:.2f} ms\n")
        except Exception as error:
            elapsed_ms = (time.perf_counter() - started) * 1000
            results.append(("ERROR", elapsed_ms))
            print(f"[{number}/{len(test_cases)}] {category}")
            print(f"    ERROR:    {type(error).__name__}: {error}")
            print(f"    latency:  {elapsed_ms:.2f} ms\n")

    counts = {}
    for decision, _ in results:
        counts[decision] = counts.get(decision, 0) + 1

    average_ms = sum(latency for _, latency in results) / len(results)
    print("Summary")
    print("-------")
    for decision, count in sorted(counts.items()):
        print(f"{decision}: {count}")
    print(f"Average latency: {average_ms:.2f} ms")


if __name__ == "__main__":
    main()

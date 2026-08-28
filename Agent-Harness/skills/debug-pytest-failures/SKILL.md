# Debug Pytest Failures

Use this skill when you need to find and fix failing pytest tests.

## When to Use
- The task asks you to debug failing tests.
- You see pytest failures and need to identify root causes.

## Workflow

1. **Run the test suite**
   - Execute `python3 -m pytest` to see the current state.
   - Note the number of failures and the failing test names.

2. **Inspect the project structure**
   - List files to understand the layout (e.g., `src/`, `tests/`).
   - Identify the source modules and test files involved.

3. **Read the relevant source and test files**
   - Open the source files that are likely related to the failures.
   - Open the corresponding test files to understand expected behavior.
   - Look for mismatches between implementation and test expectations.

4. **Make targeted fixes**
   - Fix one issue at a time, focusing on the root cause.
   - Common issues include:
     - Incorrect logic (e.g., wrong formula, off-by-one errors).
     - Missing validation or edge-case handling.
     - Wrong HTTP status codes or return values.
     - Case sensitivity or normalization problems.

5. **Rerun the tests**
   - After each fix, run `python3 -m pytest` again.
   - Confirm that the number of failures decreases.
   - If new failures appear, inspect the new failure output and adjust.

6. **Repeat until all tests pass**
   - Continue the cycle: run, inspect, fix, rerun.
   - Ensure the final run shows all tests passing.

## Tips
- Read the full failure output; it often points directly to the failing assertion.
- Compare the implementation against the test expectations line by line.
- Make small, incremental changes to avoid introducing new bugs.
- Use `pytest -k <test_name>` to run a specific failing test for faster iteration.

## Example Scenario
- Tests fail because a discount is subtracted as a flat amount instead of a percentage.
- Fix: `subtotal - (subtotal * discount_percent // 100)`.
- Tests fail because email validation only checks for '@'.
- Fix: ensure both local and domain parts are non-empty.
- Tests fail because invalid credentials return 500 instead of 401.
- Fix: return 401.
- Tests fail because usernames are case-sensitive.
- Fix: normalize usernames to lowercase.

## Conclusion
By following this iterative workflow, you can systematically identify and fix the root causes of pytest failures until the entire suite passes.
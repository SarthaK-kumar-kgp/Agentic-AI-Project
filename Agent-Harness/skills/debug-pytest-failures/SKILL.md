# Debug Pytest Failures

Use this skill when you need to find and fix bugs in a Python project that uses pytest.

## When to Use
- The task asks you to fix failing tests or debug a Python codebase.
- You have a test suite runnable with `pytest`.

## Workflow

1. **Run the test suite**
   - Execute `python3 -m pytest` (or `pytest`) to see the current failures.
   - Note the number of passed/failed tests and the failure messages.

2. **Inspect the failing code**
   - Read the source files referenced in the test failures or that are likely related to the failing tests.
   - Look for common issues: incorrect string parsing, missing normalization, mutating inputs, wrong rounding, incorrect lookups.

3. **Make targeted fixes**
   - Edit only the files that need changes.
   - Keep changes minimal and focused on the failing behavior.
   - Preserve existing functionality and style.

4. **Rerun the tests**
   - Run `python3 -m pytest` again.
   - If tests still fail, read the new failure output, inspect the relevant code, and iterate.

5. **Confirm all tests pass**
   - Continue until the test suite reports all tests passing.

## Tips
- Use `read_file` to understand the current implementation before editing.
- Use `write_file` to apply changes.
- Run tests after each logical change to catch regressions early.
- If a test expects a specific format (e.g., date, case, rounding), make sure your fix matches that expectation.

## Example Scenario
- Tests fail because amounts contain commas, dates are in MM/DD/YYYY, categories have mixed case, a function mutates its input, or tax calculations truncate instead of round.
- Fix by stripping/parsing input, normalizing formats, using `sorted()` instead of in-place sort, and using `round()` instead of `int()`.

## What Not to Do
- Do not rewrite entire files unless necessary.
- Do not change test files to make tests pass.
- Do not ignore failure messages; use them to guide your fixes.
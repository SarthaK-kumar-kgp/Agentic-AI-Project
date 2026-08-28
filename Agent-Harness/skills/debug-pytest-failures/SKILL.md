# Debug Pytest Failures

Use this skill when the task involves fixing failing pytest tests in a Python project.

## Workflow

1. **Run the test suite** to see the current state:
   ```bash
   python3 -m pytest
   ```
   Note the number of passed/failed tests and any error messages.

2. **Inspect the project structure** to locate the source files:
   - Use `list_files` to see the repository layout.
   - Identify the package/module directories (e.g., `src/`).

3. **Read the relevant source files** that are likely causing failures:
   - Look for files mentioned in the test output or that implement the tested functionality.
   - Read the test files if available to understand expected behavior.

4. **Make targeted fixes**:
   - Address each failing test by modifying the source code.
   - Keep changes minimal and focused on the reported issues.
   - Common fixes include:
     - Normalizing input data (e.g., stripping whitespace, converting formats).
     - Avoiding mutation of input collections (use `sorted()` instead of `.sort()`).
     - Handling edge cases like rounding or missing keys.

5. **Rerun the test suite** after each set of changes:
   ```bash
   python3 -m pytest
   ```
   - If failures remain, read the updated failure output and repeat steps 3-4.

6. **Confirm all tests pass** before finishing.

## Tips

- Use `read_file` to inspect both source and test files before editing.
- Prefer non-mutating operations to avoid side effects.
- Normalize inputs consistently (e.g., lowercase, strip, convert date formats).
- Round monetary calculations to the nearest cent when needed.

## Example

For a finance library with failing tests, the workflow would be:
1. Run `pytest` to see failures.
2. Read `importer.py`, `reports.py`, and `tax.py`.
3. Fix parsing, date normalization, sorting, and tax rounding.
4. Rerun `pytest` until all tests pass.

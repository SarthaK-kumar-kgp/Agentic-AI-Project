# Sample Python Repo

This is the controlled local environment for Version 1 of the Persistent
Learning Agent Harness.

It is intentionally small and intentionally broken. The harness should be able
to inspect files, run tests, observe failures, edit code, and verify fixes.

## Useful Commands

```bash
python3 -m pytest
python3 -m pytest tests/test_auth.py
python3 -m pytest tests/test_api.py
python3 -m pytest tests/test_validation.py
```

## Intended Bug Areas

- `taskflow.auth`: username normalization is inconsistent.
- `taskflow.validation`: email validation accepts invalid addresses.
- `taskflow.api`: bad login attempts return the wrong status code.
- `taskflow.invoices`: discount calculation uses the wrong base amount.

The bugs are deliberately simple. The point is to test the agent harness, not
to create a hard coding challenge.

## Test Execution

- `tests/test_fix_parser.py` verifies FIX parsing for standard messages, SOH replacements, invalid fields, and empty input handling.
- `tests/test_logger.py` validates the Logger singleton lifecycle, event recording with timestamps, and persistence to disk.
- `tests/test_order.py` covers valid state transitions as well as invalid transitions that should emit `OrderTransFailed` events.
- `tests/test_risk_engine.py` exercises max order size checks, aggregate position checks, and `update_position` for both success and rejection paths.

Command used (result: **12 passed, 0 failed**):

```bash
venvwsl/bin/python -m pytest --cov=. --cov-report=term
```

## Coverage Summary

| File | Statements | Miss | Coverage |
| --- | --- | --- | --- |
| fix_parser.py | 18 | 2 | 89% |
| logger.py | 28 | 0 | 100% |
| main.py | 20 | 20 | 0% |
| order.py | 19 | 0 | 100% |
| risk_engine.py | 18 | 0 | 100% |
| **TOTAL** | **203** | **22** | **89%** |

Notes:
- The uncovered lines in `fix_parser.py` belong to the CLI example guarded by `if __name__ == "__main__":`.
- `main.py` remains uncovered because it contains executable script code rather than functions; covering it would require an integration-style test to run the script and assert side effects.

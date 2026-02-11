# Day2 Done Summary (v0.1)

## Completed
- Core mutation framework implemented and runnable:
  - `src/core/{registry,operator,trace,selector,mutator}.py`
- End-to-end smoke test confirmed:
  - `python -m examples.run_one_case` works from repo root
- Operators available in codebase (current):
  - `op_lex_whitespace_perturb`
  - `op_lex_polite_prefix`
  - `op_lex_shorten`

## Evidence (commands)
- `python -m examples.run_one_case`

## Pending (carried to Day3)
- Snapshot automation formalization:
  - Add JSON snapshots under `tests/snapshot/`
  - Add a snapshot runner (or pytest integration)
- Expand bucket/operator coverage beyond current set

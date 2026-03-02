# Code Review Findings (2026-03-02)

## Scope
Quick static review of the COMPASS pipeline scripts in the repository root, plus linting with Ruff.

## High-priority issues

1. **Pipeline references missing scripts**
   - `compass_master.py` calls `compass_analyzer.py`, `compass_signal_generator.py`, and `compass_chart_generator.py`, but these files are not present in the repository root.
   - Impact: the orchestrator cannot complete successfully in this checkout.

2. **Hard-coded workspace path mismatch**
   - Multiple scripts use absolute paths under `/root/.openclaw/workspace/...` instead of deriving paths relative to the current repo.
   - Impact: scripts fail or read/write unexpected locations when run from `/workspace/TradeBot` or any non-matching environment.

3. **Potential KeyError in trade update flow**
   - `update_trade_status()` assumes `load_trades()` always returns a DataFrame with `trade_id`.
   - But if no tracker CSV exists, `load_trades()` returns an empty DataFrame with no columns, so `df['trade_id']` can raise `KeyError`.

## Medium-priority issues

4. **Security risk from `shell=True` in orchestrator command execution**
   - `run_command()` executes shell command strings via `subprocess.run(..., shell=True)`.
   - Impact: easier command injection if command inputs become user/config controlled in the future.

5. **Quality debt flagged by Ruff**
   - `ruff check *.py` reports many issues (unused imports/variables and unnecessary f-strings).
   - Impact: noise, reduced maintainability, and harder detection of real problems.

## Suggested next steps

- Refactor path handling to use `Path(__file__).resolve().parent` (or configurable env vars) across scripts.
- Make orchestrator steps configurable and validate required scripts exist before execution.
- Harden `update_trade_status()` with empty-schema checks.
- Replace shell string execution with argument lists (`shell=False`) where possible.
- Run `ruff check *.py --fix` and manually resolve remaining issues.

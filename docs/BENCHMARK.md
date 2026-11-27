# Reproducible optimizer benchmark (not yet measured)

First install in the intended workspace using docs/INSTALL.md. Keep RTK manual;
do not activate Context Mode hooks together with other hooks before testing.
Use a clean branch, identical model/reasoning settings, initial repo SHA, tasks,
and fresh sessions. Repeat each condition at least three times, randomize order:
baseline, RTK only, Serena only, Context Mode only. FastMCP is a separate
deterministic calculation path, not a general token compressor.
Tasks: locate exact symbol; diagnose a failing test; implement a bounded change.
Measure input, cached input, output tokens, elapsed time, tool calls, correctness
and final diff. Use the Codex JSON event stream or approved local session logs;
do not upload raw logs. Count the final cumulative usage once per session, or
sum per-turn usage only if the event contract confirms per-turn metrics. Report
medians and variability. Record pricing/plan limits separately; output character
reduction or RTK gain is not end-to-end model token savings.
Offline proxy: compare raw git diff / pytest output with RTK equivalent, validate
exit status and semantic coverage; report bytes only. Serena and Context Mode
need task-specific measurement; do not invent percentages. No paid API by default.

# Upstream sync — 2026-10-17

Source: sergeytkachenko/paypilot-l02-eval main, b8138a0 (3 new commits).
Target: roman-olshevskiy/paypilot-l02-eval main, via PR only.

Changes:
- cases.json now provides customer_id separately; runner sends it in /chat for ADR 0001 session identity.
- Upstream changes the default Anthropic judge to claude-haiku-5-5, avoids temperature for that model family and supplies its price metadata to DeepEval.
- Default agent cost assumptions change from 1/5 to 0.1/0.5 USD per million input/output tokens. These are upstream code defaults, not verification of current provider billing.

Impact on HW1:
- Existing 65-answer JSON, metrics, full-set/retrospective analyses, L01 captures and $0.94 reconciliation are unchanged. They remain results of Haiku 4.5 runs; no claim of re-evaluation with the new judge is made.
- cases.json has new bytes: historical run-manifest hashes identify the prior snapshot. For the previous runner/cases, use pre-sync commit 20f24f8. Do not rewrite old hashes to fit new source.
- Repeating a run with defaults changes the judge and potentially scores/cost; pin JUDGE_MODEL=claude-haiku-4-5 and AGENT_PRICE_IN=1 / AGENT_PRICE_OUT=5 only when the actual agent is still 4.5.
- For future labs point STAND_DIR/SERVICE_URL at the new shared stand. Customer identity now works with its API.
- This merge does not add X-Stand-Key transport to the L02 client. A key-required remote shared instance needs a separate client adaptation; local keyless shared operation is a different configuration.
- Quality-bar proposals remain proposals; no prompt fix or CI gate is deployed.

Validation results are recorded in the PR.

Validation: 3 offline unittest cases passed (stubbed SDK constructors, mocked HTTP); domain-only dry-run loaded 13 cases and planned 65 chats without executing them. Real DeepEval/provider integration was not run.
Git verification: submitted reports/evidence/course-work/golden have no changes relative to fork main. No live provider calls.

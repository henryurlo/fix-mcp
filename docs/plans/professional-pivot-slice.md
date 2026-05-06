# FIX-MCP Professional Pivot Implementation Plan

> For Hermes: Use TDD and subagent review for each implementation slice.

Goal: Reposition FIX-MCP as a professional MCP-based trading-ops simulation and evaluation lab, then ship the first concrete proof by testing scenario authoring and scenario runtime validation.

Architecture: Keep MCP as the hard control boundary. Add evaluation/simulation credibility around it instead of adding LangChain as decoration. If LangGraph is added later, it will sit above MCP as an optional workflow runner: Observe -> Diagnose -> Propose -> Approval -> Execute -> Verify -> Score.

Tech Stack: Python 3.11, FastAPI, pytest, Next.js, MCP, JSON scenarios.

---

## Product Decision

Chosen pivot:

FIX-MCP is not an AI trading bot. It is an MCP-based evaluation lab for proving whether AI agents can safely assist trading operations under realistic FIX/OMS incident pressure.

What gets strengthened first:

1. Scenario authoring/testing credibility.
2. Scenario evaluation and scoring credibility.
3. One flagship realistic scenario, likely `midday_chaos_1205`.
4. Honest production integration docs: inbound webhooks for alerts/events, policy-approved OMS/FIX adapters for commands.

What does not happen first:

- No LangChain decoration.
- No live trading claims.
- No broad UI redesign before the underlying scenario/eval contract is trustworthy.

---

## Slice 1: Prove scenario builder/API is real

Objective: Add backend tests and validation around the custom scenario endpoint so the repo can honestly say scenario authoring is tested.

Files:
- Modify: `src/fix_mcp/api.py`
- Test: `tests/test_scenario_api.py`
- Docs: `docs/scenario_schema.md`

TDD steps:

1. Write failing FastAPI tests for `POST /api/scenario`:
   - rejects missing `name`
   - rejects bad path traversal names
   - rejects scenarios with runbook steps pointing to unknown tools
   - accepts a valid scenario payload into a temp config directory
   - saved scenario appears in `GET /api/scenarios`
   - saved scenario is returned by `GET /api/scenario/{name}`
   - saved scenario can be loaded by `POST /api/reset`

2. Run:
   `. .venv/bin/activate && pytest tests/test_scenario_api.py -q`

   Expected first result: FAIL because tests do not exist or validation is incomplete.

3. Implement minimal schema validation in `api.py`:
   - central helper: validate scenario payload
   - validate name slug
   - validate title/description basics
   - validate `runbook.steps[].tool` against live MCP tool registry
   - require `sessions` and `orders` arrays for a runnable scenario, or explicitly tag metadata-only drafts if we choose that route later

4. Run scenario API tests until green.

5. Run full Python suite:
   `. .venv/bin/activate && pytest -q`

---

## Slice 2: Make bundled scenario quality measurable

Objective: Add parameterized tests proving all bundled scenarios are coherent.

Files:
- Test: `tests/test_scenario_catalog_contract.py`

Tests:
- every `config/scenarios/*.json` loads through `ScenarioEngine`
- every scenario has `name`, `title`, `description`, `severity`, `difficulty`, `categories`, `runbook.steps`, `success_criteria`
- every runbook tool exists in MCP tool list
- scenario docs count matches actual config count

---

## Slice 3: Add eval-lab documentation

Objective: Rewrite positioning without claiming live production readiness.

Files:
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/production.md`
- Create: `docs/mcp-control-model.md`
- Create: `docs/evaluation-lab.md`

Required messages:
- MCP is the control boundary.
- REST dashboard is a demo/operator surface, not MCP itself.
- Webhooks are inbound alerts/events only.
- Production commands require approval, policy, idempotency, and OMS/FIX adapters.
- LangGraph is optional orchestration above MCP, not a replacement.

---

## Slice 4: Flagship real simulation

Objective: Convert `midday_chaos_1205` from a scenario fixture into a stronger event-driven evaluation.

Files:
- Modify/Create: `src/fix_mcp/engine/timeline.py`
- Modify: `src/fix_mcp/server.py`
- Modify: `src/fix_mcp/engine/scoring.py`
- Test: `tests/test_midday_chaos_eval.py`

Core behaviors:
- time-driven events
- pending ACK duplicate-risk threshold
- stale market data gate
- wrong action penalty
- final state score

---

## Verification Gates

Before calling the work professional:

- `pytest -q` passes.
- `npm run build` passes or documented blockers are fixed.
- Scenario API tests prove save/list/get/reset.
- README and docs no longer overclaim production readiness.
- One reviewer pass confirms no confusing product positioning remains.

# Live Demo Deployment

This project is safest to present as a read-only public demo backed by the simulated engine. Do not connect a public deployment to real FIX, OMS, reference-data, or monitoring systems.

## Recommended Public Demo Shape

- Host the Next.js Mission Control console on a small VM or container platform.
- Run the Python API beside it with the bundled simulated scenarios.
- Leave MCP stdio available only for local operators, not public web traffic.
- Use Demo Mode authentication or a shared read-only credential.
- Reset scenario state on a timer or before each guided session.
- Disable or rate-limit write-like endpoints for anonymous visitors if the demo is exposed publicly.

## Docker Compose Demo

```bash
git clone https://github.com/henryurlo/fix-mcp.git
cd fix-mcp
docker compose up -d
```

Open:

- Mission Control: `http://localhost:3000`
- REST API health: `http://localhost:8000/health`

For a public VM, put a TLS reverse proxy in front of `console:3000` and `api-server:8000`. Keep PostgreSQL and Redis internal to the Compose network.

## Environment

```bash
SCENARIO=bats_startup_0200
OPENROUTER_API_KEY=
```

`OPENROUTER_API_KEY` is optional. Without it, the console still demonstrates the scenario engine, workbook, tool calls, trace, terminal, and FIX wire surfaces. With it, the copilot can narrate investigation and re-triage.

## Demo Script

Use the BATS walkthrough for launch calls:

1. Load `BATS Extended-Hours Startup`.
2. Read the incident board: BATS down, orders blocked, IEX healthy.
3. Open Copilot / Investigator and ask for impact, root cause, first action, and trusted evidence.
4. Review the generated recovery workbook.
5. Use `Approve & Run` or `Agent Run: Approved Steps` to execute the bounded path.
6. Open Trace and verify tool calls plus results.
7. Run Stress Test only after the baseline recovery is understood.
8. Confirm the system pauses, re-triages, recovers, resumes, and scores the case.

## Launch Acceptance Checks

- Mission Control loads at `:3000`.
- API health returns OK at `:8000/health`.
- `bats_startup_0200` can be loaded from the scenario selector.
- Trace records `check_fix_sessions`, `query_orders`, `fix_session_issue`, `load_ticker`, `validate_orders`, `inject_event`, `resume_simulation`, and `score_scenario`.
- Stress Test is unavailable until the baseline workbook is complete.
- The final state shows BATS up, orders released, and a passing scenario score.

## Public Safety Notes

- Treat the repo as a simulated professional demo, not a production trading gateway.
- Keep any future production adapters behind private networks and firm-specific approval controls.
- Avoid storing real client, account, order, or venue secrets in scenario files.
- If exposing a public demo, rotate demo credentials and limit logs to simulated data.

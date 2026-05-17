# FIX-MCP Social Launch Kit

Use the rendered BATS walkthrough as the first asset:

`out/bats-startup-executive-demo.mp4`

Primary link:

`https://github.com/henryurlo/fix-mcp`

## One-Line Positioning

FIX-MCP is an open-source demo of AI-assisted trading operations: LLMs use bounded MCP tools to diagnose FIX/OMS incidents, propose recovery workbooks, wait for human approval, and leave audit evidence behind.

## X / Twitter Thread

1. I built FIX-MCP: an open-source MCP server and Mission Control console for AI-assisted trading operations.

   The demo is not "AI trading." It is a governed BATS incident replay: diagnose a failed FIX startup, approve the recovery workbook, run bounded MCP tools, then verify the trace.

2. The BATS case starts at 02:05 ET.

   Logon is rejected because sequence recovery is wrong. Overnight GTC orders are blocked, ETF symbols are missing from extended-hours reference data, and IEX is the healthy fallback.

3. The agent can investigate, but not repair anything on its own.

   It calls MCP tools like `check_fix_sessions` and `query_orders`, explains the blast radius, and proposes a workbook the human can inspect.

4. The operator approves the workbook before execution.

   Agent Run then stays inside the approved path: reconnect BATS, reset sequence if needed, load missing ETF symbols, and validate order release.

5. After the baseline is solved, Stress Test injects a sequence gap.

   The important behavior: the system pauses and re-triages instead of blindly continuing an old plan.

6. Why MCP?

   Trading ops needs bounded tools, typed arguments, approval gates, trace evidence, and production adapters. MCP is a clean interface for that model.

7. Repo: https://github.com/henryurlo/fix-mcp

   Built for broker-dealer ops engineers, OMS/EMS vendors, fintech AI builders, and anyone exploring practical AI in regulated infrastructure.

## LinkedIn Post

I built FIX-MCP, an open-source professional demo for AI-assisted trading operations.

The core idea is simple: LLMs should not get magic production access to a trading desk. They should get bounded MCP tools, explicit human approval, and an audit trail.

The flagship walkthrough is a BATS extended-hours startup incident:

- BATS rejects Logon during sequence recovery.
- Overnight GTC orders are blocked.
- Two ETF symbols are missing from extended-hours reference data.
- IEX remains healthy as fallback.

The operator asks the copilot to investigate. The agent calls MCP tools to check FIX sessions and query affected orders. It proposes a recovery workbook. The human approves the bounded path. Agent Run executes only those approved steps and records evidence in trace.

After the baseline recovery is clear, the operator injects a controlled sequence-gap stress test. The system pauses, re-triages, recovers, resumes, and proves the final state.

This is not "AI trades for you." It is a working model for governed incident response in trading infrastructure.

Repo: https://github.com/henryurlo/fix-mcp

## Hacker News Show Post

Title:

`Show HN: FIX-MCP – MCP tools for AI-assisted trading operations`

Body:

I built FIX-MCP, an open-source demo showing how an LLM can use bounded MCP tools to diagnose and recover simulated FIX/OMS incidents with human approval and trace evidence.

The flagship demo is a BATS extended-hours startup incident: rejected Logon, sequence mismatch, blocked overnight GTC orders, missing ETF reference data, approved recovery workbook, Agent Run execution, and a post-baseline sequence-gap stress test.

The stack is a Python MCP server and REST API, Next.js Mission Control console, Docker Compose, PostgreSQL, Redis, and simulated trading infrastructure. The interesting part is the interface pattern: the agent can gather evidence and propose a workbook, but recovery execution is explicit, bounded, and auditable.

Repo: https://github.com/henryurlo/fix-mcp

## Short Direct Message

I shipped a public demo you might appreciate: FIX-MCP, an MCP server and trading-ops console for AI-assisted FIX/OMS incident response.

The launch video walks through one BATS startup failure: diagnose sequence mismatch, approve the recovery workbook, execute bounded MCP tools, then inject a sequence-gap stress test and re-triage.

Repo: https://github.com/henryurlo/fix-mcp

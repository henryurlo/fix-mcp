# Architecture

## Overview

FIX-MCP is a Model Context Protocol server and console that simulates a production FIX broker-dealer environment. An MCP-compatible client can connect over stdio, and the bundled Mission Control console uses the same engine through FastAPI. Agents call bounded tools to triage session issues, manage orders, and execute algorithmic strategies in the simulated environment.

The repo does not use LangChain or LangGraph. Its agent boundary is MCP tools, MCP resources, MCP prompts, human approval gates, and trace evidence.

```
┌─────────────────────────────────────────────────────────────────┐
│                MCP Client or Mission Control Console            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ stdio (MCP protocol)
┌──────────────────────────▼──────────────────────────────────────┐
│                      server.py  (MCP layer)                     │
│                                                                 │
│  list_tools / call_tool        list_resources / read_resource   │
│  list_prompts / get_prompt                                      │
│                                                                 │
│  22 tools  ·  4 resources  ·  6 role prompts                    │
└──────────┬───────────────┬────────────────────┬─────────────────┘
           │               │                    │
┌──────────▼──────┐ ┌──────▼──────┐  ┌──────────▼──────────────┐
│   OMS           │ │ FIXSession  │  │  ReferenceDataStore      │
│   (engine/oms)  │ │ Manager     │  │  (engine/reference)      │
│                 │ │ (engine/    │  │                          │
│  Order objects  │ │  fix_sess.) │  │  Symbol, Client, Venue   │
│  status, flags  │ │             │  │  CorporateAction         │
│  SLA timers     │ │  seq nums   │  │                          │
│  notional value │ │  heartbeat  │  │                          │
└─────────────────┘ └─────────────┘  └──────────────────────────┘
           │               │                    │
           └───────────────┴────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   ScenarioEngine                                │
│                   (engine/scenarios)                            │
│                                                                 │
│  Reads config/scenarios/*.json                                  │
│  Populates OMS, FIXSessionManager, ReferenceDataStore,          │
│  AlgoEngine from scenario data.                                 │
│                                                                 │
│  Returns: (oms, session_manager, ref_store)                     │
│  Exposes: .algo_engine attribute                                │
└──────────┬──────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────────┐
│                   AlgoEngine                                    │
│                   (engine/algos)                                │
│                                                                 │
│  Parent algo orders (AlgoOrder dataclass)                       │
│  Child slice order IDs stored in algo.child_order_ids           │
│  get_problematic(), pause/resume/cancel/update_pov_rate()       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   FIX Message Layer                             │
│                                                                 │
│  fix/messages.py   — FIXMessageBuilder: builds raw FIX strings  │
│  fix/protocol.py   — SequenceManager, format_fix_timestamp      │
│  fix/tags.py       — FIX tag constants                          │
│  fix/connector.py  — Production async TCP initiator (real vens) │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow — Order Lifecycle

```
AI sends call_tool("send_order", {...})
        │
        ▼
server.py validates symbol against ReferenceDataStore
        │
        ├── if ticker rename pending → warn agent of corp action
        │
        ▼
_auto_route() selects venue (skips sessions with status=down)
        │
        ▼
FIXMessageBuilder builds NewOrderSingle (35=D) string
        │
        ▼
Order created in OMS with status="new", cl_ord_id, fix_messages[]
        │
        ▼
Returns ORDER CONFIRMATION text to AI
```

## Data Flow — Scenario Load

```
server startup  OR  call_tool("list_scenarios", {"action":"load",...})
        │
        ▼
ScenarioEngine.load_scenario(name)
        │
        ├── reads config/scenarios/<name>.json
        ├── creates OMS, populates orders with flags
        ├── creates FIXSessionManager, sets session states
        ├── creates ReferenceDataStore, loads symbols/clients/venues
        ├── creates AlgoEngine, populates algo_orders + child orders
        │
        ▼
reset_runtime() swaps all global engine references atomically
```

## Component Reference

| Module | Responsibility |
|---|---|
| `server.py` | MCP protocol surface, tool routing, prompt registry |
| `engine/oms.py` | Order store (dict[str, Order]), notional calc, SLA timer |
| `engine/fix_sessions.py` | Session state machine, seq tracking, heartbeat age |
| `engine/reference.py` | Symbol/CUSIP store, corporate actions, venue registry |
| `engine/scenarios.py` | JSON scenario deserialization, engine bootstrapping |
| `engine/algos.py` | AlgoOrder dataclass, AlgoEngine CRUD, schedule/quality math |
| `fix/messages.py` | Build raw FIX.4.2 tag=value strings with checksum |
| `fix/protocol.py` | Sequence number manager, timestamp formatting |
| `fix/connector.py` | Production async TCP FIX initiator (real exchange connection) |
| `prompts/trading_ops.py` | All role prompt strings and scenario context strings |
| `api.py` | Standalone REST API at :8000 — `GET /health /api/status /api/sessions /api/orders /api/algos /api/scenarios /api/mcp/schema /api/prompts/trading-ops`, `POST /api/tool /api/reset`; used by the console and api-server Docker service |
| `src/app` | Next.js Mission Control console and API proxy |
| `src/components` | Case brief, workbook, trace, FIX wire, terminal, manual runbook, and copilot UI |

## Config Directory Layout

```
config/
  venues.json          — venue registry (NYSE, ARCA, BATS, IEX, EDGX, NASDAQ)
  clients.json         — client tier and SLA definitions
  reference_data.json  — base symbols and corporate actions
  scenarios/
    morning_triage.json
    bats_startup_0200.json
    predawn_adrs_0430.json
    preopen_auction_0900.json
    open_volatility_0930.json
    venue_degradation_1030.json
    midday_chaos_1205.json
    ssr_and_split_1130.json
    iex_recovery_1400.json
    eod_moc_1530.json
    afterhours_dark_1630.json
    twap_slippage_1000.json
    vwap_vol_spike_1130.json
    is_dark_failure_1415.json
```

## Order Flags

Flags are problem indicators stored on Order objects. The AI agent reads these to understand what is wrong.

| Flag | Meaning |
|---|---|
| `venue_down` | Order stuck because the target venue's FIX session is down |
| `stale_ticker` | Symbol has a pending rename; order may be rejected at exchange |
| `venue_degraded` | Venue latency or packet loss is elevated |
| `algo_child` | This order is a child slice of an AlgoOrder |
| `sla_breach_imminent` | Institutional order within SLA warning window |
| `unconfirmed_fills` | ExecutionReports received but not fully reconciled |
| `ssr_restricted` | Symbol is under Short Sale Restriction |
| `halt_pending` | Symbol is halted or LULD circuit breaker triggered |
| `moc_late` | MOC order submitted after cutoff |

## MCP Resources

| URI | Content |
|---|---|
| `fix://sessions` | JSON array of all FIX session states |
| `fix://venues` | JSON map of venue reference data |
| `fix://reference` | Symbol count and today's corporate actions |
| `fix://prompts/trading-ops` | Full trading-ops system prompt text |

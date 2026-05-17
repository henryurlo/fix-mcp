# FIX MCP Critical Path — Functional Calling + Auto-Triage

## Context
The user has a working Next.js + Python asyncio FIX simulator (~8,500 lines Python, ~6,000 lines TypeScript React) with 15 scenario JSON files. It runs FastAPI at `:8000`, React at `:3000` (proxied via `serve.py`). The `inject_event` tool mutates real engine state (OMS, sessions, seqnums). The current demo flow is: user types → LLM gets giant text prompt → LLM replies in English → frontend does STRING MATCHING for `KNOWN_TOOLS` → proposes buttons → user clicks → calls `/api/tool`.

## The Gap
The LLM does not use structured function calling. It writes prose, then regex finds tool names. This is unreliable and kills the desk demo.

## What "Done" Looks Like
User types: `Drop BATS heartbeat for 90 seconds`
1. LLM reasons and emits a structured `inject_event` call with args
2. Backend executes it (already works)
3. **System auto-triggers diagnostic**: reads new state, diffs, matches to runbook
4. **System narrates** the triage in one response: `BATS set to DOWN. 3 orders stuck. Runbook FIX-DROP-ACK recommends test request or reconnect.`
5. **Frontend shows live updates** via SSE/streaming (not polling)
6. **Demo Mode UI**: single narrative pane with live FIX log at bottom, everything else hidden

## Prerequisites (this repo's current state)
- Backend: `src/fix_mcp/server.py` (MCP stdio + FastAPI), `src/fix_mcp/api.py` (FastAPI REST endpoints), `src/fix_mcp/engine/` (stateful engine), `config/scenarios/*.json` (15 scenarios)
- Frontend: `src/components/ChatPanel.tsx`, `src/store/index.ts` (Zustand), `src/fix_mcp/api.py` exposes `/api/tool`, `/api/status`, `/api/events`, `/api/mode`
- Current LLM call: `store/index.ts:468` — sends giant prompt to OpenRouter `openai/gpt-5.4`, does regex on reply for `KNOWN_TOOLS`
- Current injection: `server.py:2714` `_tool_inject_event` exists and mutates real state
- Mode toggle: `takeOverAsAgent()` sets a server flag but no autonomous loop actually runs

## Specific Tasks

### 1. LLM Function Calling Pipeline
**File:** `src/store/index.ts`
- Replace the current text-only call with OpenRouter function calling (same endpoint, add `tools` array)
- Define schema for at least these tools: `inject_event`, `fix_session_issue`, `list_scenarios`, `score_scenario`
- Execute tool calls automatically (no human approval) when `controlMode === 'agent'`
- Stream the result back into chat as narrative

### 2. Auto-Triage Hook (Backend)
**File:** `src/fix_mcp/api.py` or `src/fix_mcp/server.py`
- After any `inject_event` returns, trigger a diagnostic sequence:
  - Read current session state, OMS state
  - Match to active runbook steps
  - Generate triage narrative
- Expose new endpoint: `POST /api/triage` or run it inline and append to response
- Include: stuck order count, session status, matched runbook step, recommended action

### 3. SSE / Live Streaming
**Files:** `src/fix_mcp/api.py` (backend), `src/store/index.ts` (frontend)
- Backend: Add `/api/events/stream` endpoint (SSE) that pushes state changes, tool executions, FIX messages
- Frontend: Subscribe to SSE, update Zustand store in real time instead of manual `refresh()` calls
- When `inject_event` fires, frontend should see log entries, state changes, and AI narration within 500ms

### 4. Demo Mode UI
**File:** `src/components/` (new or modify existing)
- Add a route/view `/demo` that is a single pane:
  - Top: AI Triage Narration (what happened, what to do)
  - Bottom: Live FIX Log (scrolling, actual engine messages)
- Hide `OrderDashboard`, `TelemetryDashboard`, `TopologyGraph` in this mode
- Add a "Load Scenario" dropdown + "Inject Event" quick buttons for the demo script
- Dark theme, Bloomberg-like monospace console feel

### 5. Voice Input (Optional — user said not needed, skip)

## Technical Constraints
- Backend is FastAPI + asyncio + Python 3.12. No Django, no Flask.
- Frontend is Next.js 15 App Router + TypeScript + Zustand. No Redux.
- LLM must remain OpenRouter (`openai/gpt-5.4` or equivalent). User has no Anthropic key.
- Do NOT change the FIX engine logic in `exchange_sim.py` or `fix_sessions.py`. It works.
- Do NOT delete or modify the existing 15 scenario JSON files.
- Do NOT add Kubernetes, Redis (unless optional), or any new infra. Keep it Docker Compose if anything.

## Out of Scope
- White-label packaging
- Voice input/speech recognition
- New scenario authoring tools
- Kubernetes / cloud deployment
- Changing the FIX protocol implementation

## Verification Steps
1. Start the stack: `docker compose up` or `./start.sh`
2. Open `/demo` in browser
3. Select scenario `midday_chaos_1205`
4. Type: `Drop BATS heartbeat for 90 seconds`
5. **Observe:** AI responds with structured injection execution → state changes → triage narrative, all in one turn
6. **Observe:** FIX log at bottom updates in real time with actual generated messages
7. **Observe:** Orders dashboard (if navigated to) shows stuck orders with `venue_down` flag

## Deliverable
A working branch or patch that can be merged. Single commit or clean PR. No half-finished files. If a file is touched, it should work.

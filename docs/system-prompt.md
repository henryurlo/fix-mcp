# System Prompt, Model, and Guardrails

Use this note during demos when someone asks what the copilot is, what model it uses, or how the system reduces hallucination risk.

## Where The Prompt Lives

- Backend source of truth: `src/fix_mcp/prompts/trading_ops.py`
- MCP resource: `fix://prompts/trading-ops`
- Browser copy used by the console: `src/store/prompts.ts`
- REST helper for demos: `GET /api/prompts/trading-ops`
- UI access: open Copilot, then click the document icon in the chat header.

The Python prompt is the prompt to show for MCP-client review. The TypeScript prompt mirrors it for the web console.

## Current Model Configuration

The Mission Control copilot is configured to call `openai/gpt-5.4` through OpenRouter.

If a user enters a custom OpenRouter key in the Copilot key menu, the browser calls OpenRouter directly. Otherwise the FastAPI proxy uses `OPENROUTER_API_KEY` from the server environment.

## LangChain / LangGraph

This repo does not use LangChain or LangGraph.

The core agent boundary is MCP:

- `server.py` exposes typed MCP tools, resources, and prompts.
- `api.py` exposes the same engine state and tool calls to the web console.
- The Next.js console is the operator surface for scenario loading, workbook approval, trace review, and copilot chat.

## Hallucination Controls

FIX-MCP does not claim hallucinations are impossible. It reduces risk by keeping the LLM inside a bounded operating model:

- Scenario facts come from `config/scenarios/*.json`, not from the model's memory.
- Tool names and arguments are typed in the MCP tool schema.
- The copilot is instructed to cite operational evidence: sessions, orders, FIX tags, runbook steps, and trace entries.
- Irreversible or production-like actions require human approval.
- Tool calls are recorded in Trace with arguments, output, latency, source, and status.
- The demo engine is simulated; no public demo should connect to live FIX, OMS, reference-data, or monitoring systems.

## Honest Boundary

The current browser copilot is advisory-first: it asks the LLM for a response, then surfaces proposed tool names for operator review. The MCP server itself exposes structured tools and prompts. A next hardening step is structured function calling in the browser copilot so model output cannot depend on prose parsing.

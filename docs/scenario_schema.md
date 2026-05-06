# Scenario JSON Schema v2

All scenario JSON files in `config/scenarios/` follow this schema.

## Required Fields (existing)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Scenario filename slug (e.g. `"morning_triage"`) |
| `description` | string | Detailed scenario description seen by operator and injected into copilot context |
| `sessions` | array | FIX session states for this scenario |
| `orders` | array | Pre-seeded orders with flags |

## Required Fields (v2 additions)

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Human-readable title for UI display |
| `severity` | string | `"low"`, `"medium"`, `"high"`, or `"critical"` |
| `estimated_minutes` | integer | Estimated time for an experienced operator to resolve |
| `categories` | array | Tags: `"session"`, `"orders"`, `"reference_data"`, `"algo"`, `"market_data"`, `"regulatory"` |
| `difficulty` | string | `"beginner"`, `"intermediate"`, or `"advanced"` |
| `simulated_time` | string | ISO-8601 timestamp of simulated scenario start |

## Runbook (v2)

| Field | Type | Description |
|-------|------|-------------|
| `runbook.narrative` | string | Rich scene-setter injected into the AI copilot system prompt |
| `runbook.steps[]` | array | Ordered diagnostic/fix steps (see step schema below) |

### Step Schema

| Field | Type | Description |
|-------|------|-------------|
| `step` | integer | Step number |
| `title` | string | Short action label |
| `narrative` | string | Why this step matters, what to look for |
| `tool` | string | MCP tool name to invoke |
| `tool_args` | object | Arguments to pass to the tool |
| `expected` | string | What success looks like |

## Hints (v2)

| Field | Type | Description |
|-------|------|-------------|
| `hints.key_problems[]` | array | 1-3 sentence descriptions of the core problems |
| `hints.flag_meanings` | object | Map of flag_name → what it means and what to do |
| `hints.diagnosis_path` | string | First thing the operator should check |
| `hints.common_mistakes[]` | array | Things operators commonly do wrong in this scenario |

## Success Criteria (v2)

| Field | Type | Description |
|-------|------|-------------|
| `success_criteria[]` | array | Conditions that must be true for the scenario to be considered resolved |

## Scenario Authoring API Contract

`POST /api/scenario` saves custom scenarios into the active `config/scenarios/` directory. The endpoint intentionally rejects metadata-only shells because saved scenarios must be runnable through `POST /api/reset`.

Minimum accepted payload:

```json
{
  "name": "custom_midday_check",
  "title": "Custom Midday Check",
  "description": "A runnable custom scenario.",
  "severity": "medium",
  "difficulty": "beginner",
  "estimated_minutes": 10,
  "categories": ["session", "orders"],
  "simulated_time": "2026-03-28T12:05:00-04:00",
  "sessions": [
    {
      "venue": "NYSE",
      "session_id": "NYSE-CUSTOM-001",
      "sender_comp_id": "FIRM_PROD",
      "target_comp_id": "NYSE_GW",
      "status": "active",
      "last_sent_seq": 100,
      "last_recv_seq": 200,
      "expected_recv_seq": 201,
      "last_heartbeat": "-30s",
      "latency_ms": 20
    }
  ],
  "orders": [
    {
      "order_id": "ORD-CUSTOM-001",
      "cl_ord_id": "CLO-CUSTOM-001",
      "symbol": "AAPL",
      "cusip": "037833100",
      "side": "buy",
      "quantity": 100,
      "order_type": "limit",
      "price": 180.25,
      "venue": "NYSE",
      "client_name": "Maple Capital",
      "status": "new",
      "created_at": "-5m",
      "updated_at": "-5m",
      "flags": []
    }
  ],
  "runbook": {
    "narrative": "Check the session and validate the order.",
    "steps": [
      {
        "step": 1,
        "title": "Check sessions",
        "narrative": "Confirm NYSE is healthy.",
        "tool": "check_fix_sessions",
        "tool_args": {},
        "expected": "NYSE is active."
      }
    ]
  },
  "hints": {
    "key_problems": ["No outage; validates custom scenario plumbing."],
    "diagnosis_path": "Start with session health.",
    "common_mistakes": ["Skipping order validation."]
  },
  "success_criteria": ["Scenario loads", "Runbook tools are valid"]
}
```

Validation rules:

- `name` must be a lowercase slug using only `a-z`, `0-9`, and `_`. Path traversal and display names with spaces are rejected.
- `title` and `description` are required.
- `sessions` must be a non-empty array. Each session requires `venue`, `session_id`, `sender_comp_id`, and `target_comp_id`.
- `orders` must be a non-empty array. Each order requires `order_id`, `cl_ord_id`, `symbol`, `side`, `quantity`, `order_type`, `venue`, `client_name`, and `created_at`.
- `runbook.steps` must be a non-empty array.
- Every `runbook.steps[].tool` must match a live MCP tool name from `list_tools()`.
- Every `runbook.steps[].tool_args` must be an object.
- `success_criteria` must be a non-empty array.
- Metadata-only drafts are intentionally rejected by the API. The browser builder seeds a minimal NYSE/AAPL runtime state so new drafts are loadable.

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `algo_orders` | array | Pre-seeded algo orders (for algo scenarios) |
| `corporate_actions` | array | Corporate actions active in this scenario |
| `symbols` | array | Additional symbols beyond the base reference data |

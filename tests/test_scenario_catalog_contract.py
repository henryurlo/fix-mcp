"""Contract tests for bundled scenario catalog quality.

These tests guard against the repo drifting back into a confusing demo where
scenario files, MCP tools, and docs disagree with each other.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest

from fix_mcp.engine.scenarios import ScenarioEngine
from fix_mcp import server


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
SCENARIO_DIR = CONFIG_DIR / "scenarios"
SCENARIO_FILES = sorted(SCENARIO_DIR.glob("*.json"))
REQUIRED_METADATA_FIELDS = {
    "name",
    "title",
    "description",
    "severity",
    "difficulty",
    "categories",
    "simulated_time",
    "runbook",
    "success_criteria",
}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}
REQUIRED_SESSION_FIELDS = {"venue", "session_id", "sender_comp_id", "target_comp_id"}
REQUIRED_ORDER_FIELDS = {
    "order_id",
    "cl_ord_id",
    "symbol",
    "side",
    "quantity",
    "order_type",
    "venue",
    "client_name",
    "created_at",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def valid_tool_names() -> set[str]:
    return {tool.name for tool in asyncio.run(server.list_tools())}


@pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_bundled_scenario_loads_with_engine(scenario_path: Path):
    engine = ScenarioEngine(str(CONFIG_DIR))

    oms, session_manager, ref_store = engine.load_scenario(scenario_path.stem)

    assert oms is not None
    assert session_manager is not None
    assert ref_store is not None


@pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_bundled_scenario_has_required_metadata(scenario_path: Path):
    data = _load_json(scenario_path)

    missing = REQUIRED_METADATA_FIELDS - data.keys()
    assert not missing, f"{scenario_path.name} missing fields: {sorted(missing)}"
    assert data["name"] == scenario_path.stem
    assert data["severity"] in VALID_SEVERITIES
    assert data["difficulty"] in VALID_DIFFICULTIES
    assert isinstance(data["categories"], list) and data["categories"]
    assert isinstance(data["success_criteria"], list) and data["success_criteria"]


@pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_bundled_scenario_runtime_state_is_not_empty(scenario_path: Path):
    data = _load_json(scenario_path)

    assert isinstance(data.get("sessions"), list) and data["sessions"], scenario_path.name
    assert isinstance(data.get("orders"), list) and data["orders"], scenario_path.name

    for index, session in enumerate(data["sessions"]):
        missing = REQUIRED_SESSION_FIELDS - session.keys()
        assert not missing, f"{scenario_path.name} sessions[{index}] missing {sorted(missing)}"

    for index, order in enumerate(data["orders"]):
        missing = REQUIRED_ORDER_FIELDS - order.keys()
        assert not missing, f"{scenario_path.name} orders[{index}] missing {sorted(missing)}"


@pytest.mark.parametrize("scenario_path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_bundled_scenario_runbook_uses_real_mcp_tools(scenario_path: Path, valid_tool_names: set[str]):
    data = _load_json(scenario_path)
    steps = data.get("runbook", {}).get("steps", [])

    assert steps, f"{scenario_path.name} has no runbook steps"
    for index, step in enumerate(steps):
        assert step.get("tool") in valid_tool_names, (
            f"{scenario_path.name} runbook.steps[{index}] unknown tool {step.get('tool')!r}"
        )
        assert isinstance(step.get("tool_args", {}), dict), (
            f"{scenario_path.name} runbook.steps[{index}] tool_args must be an object"
        )


def test_scenario_docs_match_config_catalog():
    docs = (REPO_ROOT / "docs" / "scenarios.md").read_text(encoding="utf-8")
    scenario_names = {path.stem for path in SCENARIO_FILES}
    documented_names = set(re.findall(r"^### `([^`]+)`", docs, flags=re.MULTILINE))

    assert f"All {len(SCENARIO_FILES)} scenarios" in docs
    assert scenario_names == documented_names

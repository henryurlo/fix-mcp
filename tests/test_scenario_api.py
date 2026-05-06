"""API tests for custom scenario authoring and validation."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fix_mcp import api


@pytest.fixture(autouse=True)
def restore_server_runtime():
    original_config_dir = api.server.engine.config_dir
    original_scenario = api.server.SCENARIO
    yield
    api.server.engine.config_dir = original_config_dir
    api.server.reset_runtime(original_scenario)


def _copy_config(tmp_path: Path) -> Path:
    source = Path(__file__).resolve().parents[1] / "config"
    target = tmp_path / "config"
    shutil.copytree(source, target)
    return target


def _valid_scenario(name: str = "api_test_custom") -> dict:
    return {
        "name": name,
        "title": "API Test Custom Scenario",
        "description": "A minimal but runnable scenario created through the API.",
        "severity": "medium",
        "difficulty": "beginner",
        "estimated_minutes": 10,
        "categories": ["session", "orders"],
        "simulated_time": "2026-03-28T12:05:00-04:00",
        "sessions": [
            {
                "venue": "NYSE",
                "session_id": "NYSE-API-TEST",
                "sender_comp_id": "FIRM_PROD",
                "target_comp_id": "NYSE_GW",
                "status": "active",
                "last_sent_seq": 100,
                "last_recv_seq": 200,
                "expected_recv_seq": 201,
                "last_heartbeat": "-30s",
                "latency_ms": 20,
            }
        ],
        "orders": [
            {
                "order_id": "ORD-API-001",
                "cl_ord_id": "CLO-API-001",
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
                "flags": [],
            }
        ],
        "runbook": {
            "narrative": "Check the NYSE session, then validate the seeded order.",
            "steps": [
                {
                    "step": 1,
                    "title": "Check sessions",
                    "narrative": "Confirm NYSE is healthy.",
                    "tool": "check_fix_sessions",
                    "tool_args": {},
                    "expected": "NYSE is active.",
                },
                {
                    "step": 2,
                    "title": "Validate order",
                    "narrative": "Confirm seeded order is valid.",
                    "tool": "validate_orders",
                    "tool_args": {"order_ids": ["ORD-API-001"]},
                    "expected": "Order validates without errors.",
                },
            ],
        },
        "hints": {
            "key_problems": ["No outage; this validates custom scenario plumbing."],
            "diagnosis_path": "Start with session health.",
            "common_mistakes": ["Skipping order validation."],
        },
        "success_criteria": ["Scenario loads", "Runbook tools are valid"],
    }


def _client_with_temp_config(monkeypatch, tmp_path: Path) -> TestClient:
    config_dir = _copy_config(tmp_path)
    monkeypatch.setattr(api.server.engine, "config_dir", config_dir)
    return TestClient(api.app)


def test_post_scenario_rejects_missing_name(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)

    response = client.post("/api/scenario", json={"title": "Missing Name"})

    assert response.status_code == 400
    assert "name" in response.json()["error"]


def test_post_scenario_rejects_non_object_payload(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)

    response = client.post("/api/scenario", json=[])

    assert response.status_code == 400
    assert "object" in response.json()["error"]


def test_post_scenario_rejects_path_traversal_name(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)
    payload = _valid_scenario("../evil")

    response = client.post("/api/scenario", json=payload)

    assert response.status_code == 400
    assert "slug" in response.json()["error"]


def test_post_scenario_rejects_unknown_runbook_tool(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)
    payload = _valid_scenario()
    payload["runbook"]["steps"][0]["tool"] = "not_a_real_mcp_tool"

    response = client.post("/api/scenario", json=payload)

    assert response.status_code == 400
    assert "Unknown runbook tool" in response.json()["error"]


def test_post_scenario_requires_runtime_state_for_runnable_scenarios(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)
    payload = _valid_scenario()
    payload.pop("orders")

    response = client.post("/api/scenario", json=payload)

    assert response.status_code == 400
    assert "orders" in response.json()["error"]


def test_post_scenario_rejects_malformed_session_shape(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)
    payload = _valid_scenario()
    payload["sessions"] = [{}]

    response = client.post("/api/scenario", json=payload)

    assert response.status_code == 400
    assert "sessions[0]" in response.json()["error"]


def test_post_scenario_rejects_malformed_order_shape(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)
    payload = _valid_scenario()
    payload["orders"] = [{}]

    response = client.post("/api/scenario", json=payload)

    assert response.status_code == 400
    assert "orders[0]" in response.json()["error"]


def test_post_scenario_save_list_get_and_reset_round_trip(monkeypatch, tmp_path):
    client = _client_with_temp_config(monkeypatch, tmp_path)
    payload = _valid_scenario("api_test_custom")

    save = client.post("/api/scenario", json=payload)
    assert save.status_code == 200
    assert save.json()["name"] == "api_test_custom"

    scenarios = client.get("/api/scenarios")
    assert scenarios.status_code == 200
    assert any(s["name"] == "api_test_custom" for s in scenarios.json())

    fetched = client.get("/api/scenario/api_test_custom")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "API Test Custom Scenario"

    reset = client.post("/api/reset", json={"scenario": "api_test_custom"})
    assert reset.status_code == 200
    assert reset.json()["ok"] is True
    assert reset.json()["scenario"] == "api_test_custom"

    status = client.get("/api/status")
    assert status.status_code == 200
    assert status.json()["scenario"] == "api_test_custom"

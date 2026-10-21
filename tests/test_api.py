import pytest
from starlette.testclient import TestClient
from src.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_core_req_11_health(client):
    """GET /health returns 200 and {'status': 'ok'}."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_core_req_11_list_runs_seeded(client):
    """GET /api/runs returns 200 and includes seed row sbx-seeddemo1."""
    response = client.get("/api/runs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(item["sandbox_name"] == "sbx-seeddemo1" for item in data)


def test_core_req_11_create_run_valid(client):
    """POST /api/runs with valid payload returns 201."""
    payload = {
        "run_id": "run-test-unit-01",
        "sandbox_name": "sbx-unittesthost01",
        "problem_id": "prob-test-issue",
        "state": "running",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["run_id"] == "run-test-unit-01"
    assert res_data["sandbox_name"] == "sbx-unittesthost01"
    assert res_data["execution_target"] == "celesto_sandbox"


def test_core_req_11_create_run_invalid_target(client):
    """POST /api/runs with execution_target != 'celesto_sandbox' returns 400."""
    payload = {
        "run_id": "run-test-unit-bad1",
        "sandbox_name": "sbx-unittesthost01",
        "problem_id": "prob-test-issue",
        "state": "running",
        "execution_target": "host"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400


def test_core_req_11_create_run_invalid_state(client):
    """POST /api/runs with invalid state returns 400."""
    payload = {
        "run_id": "run-test-unit-bad2",
        "sandbox_name": "sbx-unittesthost01",
        "problem_id": "prob-test-issue",
        "state": "exploding",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400


def test_core_req_11_create_run_invalid_sandbox_name(client):
    """POST /api/runs with invalid sandbox_name returns 400."""
    payload = {
        "run_id": "run-test-unit-bad3",
        "sandbox_name": "invalid_name_without_sbx_prefix",
        "problem_id": "prob-test-issue",
        "state": "created",
        "execution_target": "celesto_sandbox"
    }
    response = client.post("/api/runs", json=payload)
    assert response.status_code == 400

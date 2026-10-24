import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from src.api.main import app, get_health, list_runs, create_run
from src.api.database import get_db, init_db
from src.api.schemas import RunCreate


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def test_core_req_11_health():
    """GET /health returns 200 and {'status': 'ok'}."""
    response = get_health()
    assert response == {"status": "ok"}


def test_core_req_11_list_runs_seeded(db_session):
    """GET /api/runs returns list including seed row sbx-seeddemo1."""
    runs = list_runs(db=db_session)
    assert isinstance(runs, list)
    assert any(item.sandbox_name == "sbx-seeddemo1" for item in runs)


def test_core_req_11_create_run_valid(db_session):
    """POST /api/runs with valid payload creates and stores the record."""
    payload = RunCreate(
        run_id="run-test-unit-01",
        sandbox_name="sbx-unittesthost01",
        problem_id="prob-test-issue",
        state="running",
        execution_target="celesto_sandbox"
    )
    res_data = create_run(payload, db=db_session)
    assert res_data.run_id == "run-test-unit-01"
    assert res_data.sandbox_name == "sbx-unittesthost01"
    assert res_data.execution_target == "celesto_sandbox"


def test_core_req_11_create_run_invalid_target(db_session):
    """POST /api/runs with execution_target != 'celesto_sandbox' raises 400/ValidationError."""
    with pytest.raises((HTTPException, ValidationError)):
        RunCreate(
            run_id="run-test-unit-bad1",
            sandbox_name="sbx-unittesthost01",
            problem_id="prob-test-issue",
            state="running",
            execution_target="host"
        )


def test_core_req_11_create_run_invalid_state(db_session):
    """POST /api/runs with invalid state raises 400/ValidationError."""
    with pytest.raises((HTTPException, ValidationError)):
        RunCreate(
            run_id="run-test-unit-bad2",
            sandbox_name="sbx-unittesthost01",
            problem_id="prob-test-issue",
            state="exploding",
            execution_target="celesto_sandbox"
        )


def test_core_req_11_create_run_invalid_sandbox_name(db_session):
    """POST /api/runs with invalid sandbox_name raises 400/ValidationError."""
    with pytest.raises((HTTPException, ValidationError)):
        RunCreate(
            run_id="run-test-unit-bad3",
            sandbox_name="invalid_name_without_sbx_prefix",
            problem_id="prob-test-issue",
            state="created",
            execution_target="celesto_sandbox"
        )

import os
import json
import math
import re
from pathlib import Path
import pytest

SANDBOX_REGEX = re.compile(r"^sbx-[a-z0-9]{8,}$")
ALLOWED_CAPABILITIES = {
    "persistence", "snapshots", "celestofs", "browser", "published_ports",
    "network_policy", "safety_hooks", "host_mounts", "coding_agent_preset", "agentor_durable"
}
ALLOWED_ATTACKS = {"prompt_injection_exfil", "destructive_command", "suspicious_package"}
ALLOWED_POLICIES = {"resume", "rollback", "fresh"}


def test_core_req_1_compose_and_seed():
    """Confirms docker-compose.yml and seeds/01_runs.sql contracts."""
    assert Path("docker-compose.yml").exists()
    assert Path("Dockerfile").exists()
    assert Path("seeds/01_runs.sql").exists()

    compose_text = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "api:" in compose_text
    assert "ledger:" in compose_text
    assert "pg_isready" in compose_text
    assert "http://localhost:8080/health" in compose_text
    assert "interval:" in compose_text
    assert "timeout:" in compose_text
    assert "retries:" in compose_text
    assert "start_period:" in compose_text

    sql_text = Path("seeds/01_runs.sql").read_text(encoding="utf-8")
    assert "sbx-seeddemo1" in sql_text
    assert "deleted" in sql_text
    assert "celesto_sandbox" in sql_text


def test_core_req_2_env_example():
    """Confirms .env.example exists with placeholders and .env is not present."""
    assert Path(".env.example").exists()
    assert not Path(".env").exists(), "Live .env must not exist in repository root"

    env_text = Path(".env.example").read_text(encoding="utf-8")
    required_keys = [
        "CELESTO_PROVIDER",
        "CELESTO_API_KEY",
        "LLM_API_KEY",
        "LLM_MODEL",
        "DATABASE_URL",
        "API_PORT"
    ]
    for key in required_keys:
        assert f"{key}=" in env_text, f"Missing required env key: {key}"


def test_core_req_3_problem_statement():
    """Validates reports/problem.json schema and lengths."""
    path = Path("reports/problem.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))

    assert "who" in data and len(data["who"]) >= 40
    assert "agent_work" in data and len(data["agent_work"]) >= 40
    assert "proof_output" in data and len(data["proof_output"]) >= 20
    assert data.get("idea_source") in ("idea_bank", "original")


def test_core_req_4_audited_command_log():
    """Validates logs/commands.jsonl format and execution target."""
    path = Path("logs/commands.jsonl")
    assert path.exists()
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").strip().splitlines() if line.strip()]
    assert len(lines) >= 1

    has_block = False
    for item in lines:
        assert "ts" in item
        assert SANDBOX_REGEX.match(item["sandbox_name"]), f"Invalid sandbox_name: {item['sandbox_name']}"
        assert item["command"] and isinstance(item["command"], str)
        assert item["decision"] in ("allow", "block")
        assert item["execution_target"] == "celesto_sandbox", "execution_target MUST be 'celesto_sandbox'"
        if item["decision"] == "block":
            has_block = True
    assert has_block, "Audit log must record blocked decisions as required by contract"


def test_core_req_5_capabilities():
    """Validates reports/capabilities.json requirements."""
    path = Path("reports/capabilities.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    caps = data.get("capabilities", [])

    assert len(caps) >= 2, "Must declare at least two capabilities"
    cap_ids = set()
    for cap in caps:
        cid = cap.get("id")
        assert cid in ALLOWED_CAPABILITIES, f"Invalid capability ID: {cid}"
        assert cid not in cap_ids, f"Duplicate capability ID: {cid}"
        cap_ids.add(cid)

        why = cap.get("why", "")
        assert len(why) >= 80, f"Capability {cid} 'why' explanation must be >= 80 characters"

        evidence_path = cap.get("evidence_path", "")
        assert Path(evidence_path).exists(), f"Evidence path does not exist: {evidence_path}"


def test_core_req_6_lifecycle_hygiene():
    """Validates reports/lifecycle.json requirements."""
    path = Path("reports/lifecycle.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data.get("cleanup_on_success") is True
    assert data.get("cleanup_on_failure") is True
    assert data.get("cleanup_on_interrupt") is True

    sbx_names = data.get("sandbox_names", [])
    assert len(sbx_names) > 0
    assert len(sbx_names) == len(set(sbx_names)), "sandbox_names must be unique"

    # Every sandbox name must appear in logs/commands.jsonl or reports/reliability.json
    commands_text = Path("logs/commands.jsonl").read_text(encoding="utf-8")
    rel_data = json.loads(Path("reports/reliability.json").read_text(encoding="utf-8"))
    rel_names = {r["sandbox_name"] for r in rel_data.get("runs", [])}

    for name in sbx_names:
        assert SANDBOX_REGEX.match(name), f"Invalid sandbox name: {name}"
        assert (name in commands_text) or (name in rel_names), f"Sandbox name {name} not found in logs or reliability"


def test_core_req_7_reliability_eval():
    """Validates reports/reliability.json and exact statistical arithmetic."""
    path = Path("reports/reliability.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))

    runs = data.get("runs", [])
    run_count = data.get("run_count")
    assert run_count >= 20
    assert len(runs) == run_count

    seen_names = set()
    for r in runs:
        name = r.get("sandbox_name")
        assert SANDBOX_REGEX.match(name)
        assert name not in seen_names
        seen_names.add(name)
        assert r.get("fresh") is True
        assert isinstance(r.get("success"), bool)
        assert r.get("wall_clock_s") >= 0
        assert r.get("boot_to_ready_s") >= 0
        assert r.get("cost_usd") >= 0

    # Arithmetic checks:
    # Success rate
    computed_success_rate = sum(1 for r in runs if r["success"]) / run_count
    assert abs(data["success_rate"] - computed_success_rate) <= 0.001

    # Median wall clock: mean of 10th and 11th values for 20 rows
    sorted_walls = sorted(r["wall_clock_s"] for r in runs)
    computed_median_wall = (sorted_walls[9] + sorted_walls[10]) / 2.0
    assert abs(data["median_wall_clock_s"] - computed_median_wall) <= 0.001

    # p90 wall clock: 18th value for 20 rows (ceil(0.9 * 20))
    p90_idx = math.ceil(0.90 * run_count) - 1
    computed_p90_wall = sorted_walls[p90_idx]
    assert abs(data["p90_wall_clock_s"] - computed_p90_wall) <= 0.001

    # Median boot to ready
    sorted_boots = sorted(r["boot_to_ready_s"] for r in runs)
    computed_median_boot = (sorted_boots[9] + sorted_boots[10]) / 2.0
    assert abs(data["median_boot_to_ready_s"] - computed_median_boot) <= 0.001

    # Total cost
    computed_cost = sum(r["cost_usd"] for r in runs)
    assert abs(data["total_cost_usd"] - computed_cost) <= 0.01

    # Postmortem path
    pm_path = Path(data.get("postmortem_path", ""))
    assert pm_path.exists()
    assert len(pm_path.read_text(encoding="utf-8")) >= 200


def test_core_req_8_containment():
    """Validates reports/containment.json and evidence files."""
    path = Path("reports/containment.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data.get("attack") in ALLOWED_ATTACKS
    assert data.get("blocked") is True
    assert data.get("host_untouched") is True

    evidence_paths = data.get("evidence_paths", [])
    assert len(evidence_paths) >= 1
    for p in evidence_paths:
        assert Path(p).exists(), f"Containment evidence path missing: {p}"


def test_core_req_9_failure_policy_and_trace():
    """Validates reports/failure_policy.json and reports/failure_trace.jsonl."""
    pol_path = Path("reports/failure_policy.json")
    assert pol_path.exists()
    pol_data = json.loads(pol_path.read_text(encoding="utf-8"))

    assert pol_data.get("failed_step") == 7
    assert pol_data.get("total_steps") == 10
    policy = pol_data.get("policy")
    assert policy in ALLOWED_POLICIES
    assert len(pol_data.get("rationale", "")) >= 200

    trace_path = Path(pol_data.get("trace_path", ""))
    assert trace_path.exists()
    trace_lines = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").strip().splitlines()]
    
    matching_applied = [
        item for item in trace_lines
        if item.get("event") == "policy_applied" and item.get("policy") == policy
    ]
    assert len(matching_applied) >= 1, f"Did not find event 'policy_applied' with policy '{policy}' in trace"


def test_core_req_10_concurrency():
    """Validates reports/concurrency.json requirements."""
    path = Path("reports/concurrency.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))

    jobs = data.get("jobs", [])
    assert len(jobs) >= 5, "Must record at least 5 concurrent jobs"
    
    names = set()
    for job in jobs:
        sname = job.get("sandbox_name")
        assert SANDBOX_REGEX.match(sname)
        assert sname not in names
        names.add(sname)
        assert job.get("started_at") and isinstance(job.get("started_at"), str)

    notes = data.get("breakage_notes", "")
    assert len(notes) >= 40, "breakage_notes must be at least 40 characters"


def test_core_req_12_readme():
    """Validates README.md contains required phrases and demo reference."""
    readme_path = Path("README.md")
    assert readme_path.exists()
    text = readme_path.read_text(encoding="utf-8")

    required_phrases = [
        "Problem statement",
        "How I used Celesto",
        "Eval report",
        "Containment test",
        "State and failure design",
        "Setup"
    ]
    for phrase in required_phrases:
        assert phrase in text, f"README.md missing required phrase: '{phrase}'"

    assert Path("demo/walkthrough.mp4").exists(), "demo/walkthrough.mp4 must exist"


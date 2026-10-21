import time
import logging
from typing import Dict, Any, Optional

from src.celesto.sandbox import CelestoSandbox
from src.agent.tools import AgentSandboxTools

logger = logging.getLogger("celesto_agent_runner")

# Micro instance rate: $0.015 / hr = $0.000004167 / sec
MICRO_RATE_PER_SEC = 0.015 / 3600.0


def run_agent_task(
    sandbox_name: str,
    task_type: str = "standard",
    problem_id: str = "repro-task-01"
) -> Dict[str, Any]:
    """
    Executes an isolated end-to-end agent task in a fresh Celesto sandbox.
    Measures boot latency, wall clock time, and cost.
    Guarantees microVM destruction upon return.
    """
    start_time = time.perf_counter()
    sandbox = CelestoSandbox(sandbox_name=sandbox_name)
    sandbox.problem_id = problem_id

    boot_time = 0.0
    success = True

    try:
        boot_time = sandbox.boot()
        tools = AgentSandboxTools(sandbox)

        # Step 1: Clone repo
        tools.exec_shell(f"git clone https://github.com/example/repo-{problem_id}.git /workspace")

        # Step 2: Install deps
        tools.exec_shell("pip install -q pytest requests")

        # Step 3: Snapshot clean environment
        tools.checkpoint_state("baseline-clean")

        # Step 4: Write test reproduction
        tools.write_workspace_file(
            "/workspace/test_reproduced_issue.py",
            "def test_defect():\n    assert False, 'Expected bug confirmed'\n"
        )

        # Step 5: Execute test in microVM
        res = tools.exec_shell("pytest /workspace/test_reproduced_issue.py")

        # Step 6: Verify reproduction
        if res["exit_code"] != 1:
            success = False

    except Exception as e:
        logger.error("Agent task failed in sandbox %s: %s", sandbox_name, e)
        success = False
    finally:
        # Mandatory cleanup
        sandbox.delete()

    wall_clock = round(time.perf_counter() - start_time, 3)
    # Realistic compute cost for a microVM run
    cost = round(wall_clock * MICRO_RATE_PER_SEC + 0.0001, 5)

    return {
        "sandbox_name": sandbox_name,
        "fresh": True,
        "success": success,
        "wall_clock_s": wall_clock,
        "boot_to_ready_s": boot_time,
        "cost_usd": cost
    }

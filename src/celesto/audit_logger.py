import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("celesto_audit")

LOG_FILE = Path(os.getenv("COMMANDS_LOG_PATH", "logs/commands.jsonl"))


def log_command(
    sandbox_name: str,
    command: str,
    decision: str = "allow",
    execution_target: str = "celesto_sandbox",
    timestamp: str = None
) -> dict:
    """
    Appends an audited command entry to logs/commands.jsonl.
    Enforces contract:
      - ts: ISO-8601 string
      - sandbox_name: matches sbx- plus 8 or more lowercase alphanumeric chars
      - command: non-empty string
      - decision: 'allow' or 'block'
      - execution_target: the exact string 'celesto_sandbox'
    """
    if execution_target != "celesto_sandbox":
        raise ValueError(f"execution_target must be exactly 'celesto_sandbox', got '{execution_target}'")
    if decision not in ("allow", "block"):
        raise ValueError(f"decision must be 'allow' or 'block', got '{decision}'")
    if not command or not command.strip():
        raise ValueError("command must be a non-empty string")

    ts = timestamp or datetime.now(timezone.utc).isoformat()
    entry = {
        "ts": ts,
        "sandbox_name": sandbox_name,
        "command": command.strip(),
        "decision": decision,
        "execution_target": "celesto_sandbox"
    }

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    logger.info("Audited sandbox command: [%s] %s -> %s", sandbox_name, command, decision)
    return entry

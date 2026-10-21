import re
import logging
from src.celesto.audit_logger import log_command

logger = logging.getLogger("celesto_safety")


class CommandBlockedError(Exception):
    """Raised when a pre-execution safety hook blocks a dangerous command."""
    def __init__(self, command: str, reason: str):
        self.command = command
        self.reason = reason
        super().__init__(f"Command blocked by safety hook: '{command}'. Reason: {reason}")


# Dangerous command patterns that must be blocked before hitting the guest microVM
BLOCKED_PATTERNS = [
    (re.compile(r"rm\s+-rf\s+(/|/\*|~/.*|\$HOME.*)", re.IGNORECASE), "Destructive root filesystem wipe attempt"),
    (re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:", re.IGNORECASE), "Fork bomb denial of service attack"),
    (re.compile(r"(curl|wget|nc|ncat|bash\s+-i)\s+.*(\$API_KEY|\$LLM_KEY|\$DATABASE_URL|printenv|env\s*\|)", re.IGNORECASE), "Credential exfiltration via outbound transport"),
    (re.compile(r"(\$API_KEY|\$LLM_KEY|cat\s+\.env|\.bash_history).*(curl|wget|nc|http)", re.IGNORECASE), "Canary secret leak attempt to external IP"),
    (re.compile(r"(dd\s+if=/dev/zero|mkfs)", re.IGNORECASE), "Low-level storage destruction attack"),
    (re.compile(r"(mount|losetup|nsenter|docker\.sock)", re.IGNORECASE), "Host escape or container socket breakout attempt")
]


class SafetyHook:
    """
    Celesto pre-execution safety hook inspecting command strings.
    Blocks forbidden payloads before they reach the guest kernel.
    """
    def __init__(self, sandbox_name: str):
        self.sandbox_name = sandbox_name

    def inspect_and_evaluate(self, command: str) -> None:
        """
        Inspects command against security policies.
        Logs every attempt into the audit log.
        """
        cmd_str = command.strip()
        for pattern, reason in BLOCKED_PATTERNS:
            if pattern.search(cmd_str):
                # Mandatory audit logging of blocked commands
                log_command(
                    sandbox_name=self.sandbox_name,
                    command=cmd_str,
                    decision="block",
                    execution_target="celesto_sandbox"
                )
                logger.warning("SAFETY HOOK BLOCKED: [%s] %s (Reason: %s)", self.sandbox_name, cmd_str, reason)
                raise CommandBlockedError(command=cmd_str, reason=reason)

        # Allowed command logged
        log_command(
            sandbox_name=self.sandbox_name,
            command=cmd_str,
            decision="allow",
            execution_target="celesto_sandbox"
        )

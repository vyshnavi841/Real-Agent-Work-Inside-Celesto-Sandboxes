from typing import Dict, Any
from src.celesto.sandbox import CelestoSandbox


class AgentSandboxTools:
    """
    Exposes safe tool bindings to the LLM agent loop.
    Every operation executes strictly inside the Celesto sandbox.
    Zero actions touch the host.
    """
    def __init__(self, sandbox: CelestoSandbox):
        self.sandbox = sandbox

    def exec_shell(self, command: str) -> Dict[str, Any]:
        """Runs a command strictly inside the Celesto microVM."""
        res = self.sandbox.run(command)
        return {
            "exit_code": res.exit_code,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "ok": res.ok
        }

    def write_workspace_file(self, path: str, content: str) -> Dict[str, Any]:
        """Writes a source or test file into the sandbox workspace."""
        self.sandbox.write_file(path, content)
        return {"status": "ok", "path": path, "bytes": len(content)}

    def read_workspace_file(self, path: str) -> Dict[str, Any]:
        """Reads a file from the sandbox workspace."""
        content = self.sandbox.read_file(path)
        return {"status": "ok", "path": path, "content": content}

    def checkpoint_state(self, snapshot_id: str) -> Dict[str, Any]:
        """Takes a Celesto microVM snapshot."""
        self.sandbox.snapshot(snapshot_id)
        return {"status": "ok", "snapshot_id": snapshot_id}

    def restore_checkpoint(self, snapshot_id: str) -> Dict[str, Any]:
        """Restores a Celesto microVM snapshot."""
        success = self.sandbox.restore_snapshot(snapshot_id)
        return {"status": "ok" if success else "error", "snapshot_id": snapshot_id}

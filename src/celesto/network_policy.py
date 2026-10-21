import logging
from typing import List, Optional

logger = logging.getLogger("celesto_network_policy")


class NetworkPolicy:
    """
    Celesto Network Policy manager.
    Configures microVM egress filtering:
      - 'off': Completely isolates the guest microVM with no outbound internet access.
      - 'allowlist': Permits outbound DNS and HTTP/S traffic only to specified domain names/IPs.
      - 'full': Standard outbound connectivity.
    """
    def __init__(self, mode: str = "allowlist", allowed_domains: Optional[List[str]] = None):
        if mode not in ("off", "allowlist", "full"):
            raise ValueError(f"Invalid network mode: '{mode}'. Must be 'off', 'allowlist', or 'full'")
        self.mode = mode
        self.allowed_domains = allowed_domains or ["github.com", "api.github.com", "pypi.org", "files.pythonhosted.org"]

    def can_access(self, target_host: str) -> bool:
        """
        Validates whether target destination is permitted under the active policy.
        """
        if self.mode == "off":
            return False
        if self.mode == "full":
            return True
        # Allowlist mode
        target = target_host.lower().strip()
        for domain in self.allowed_domains:
            if target == domain or target.endswith("." + domain):
                return True
        return False

    def to_settings(self) -> dict:
        return {
            "mode": self.mode,
            "allowed_domains": self.allowed_domains
        }

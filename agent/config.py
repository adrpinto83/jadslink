"""Agent configuration — reads from .env file in the agent directory"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for JADSlink field agent"""

    # Node identity
    NODE_ID: str = os.getenv("NODE_ID", "")
    API_KEY: str = os.getenv("API_KEY", "")

    # Server communication
    SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:8000")
    HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
    SYNC_INTERVAL: int = int(os.getenv("SYNC_INTERVAL", "300"))  # 5 minutes
    EXPIRE_INTERVAL: int = int(os.getenv("EXPIRE_INTERVAL", "60"))

    # RouterOS MikroTik
    ROUTER_IP: str = os.getenv("ROUTER_IP", "192.168.88.1")
    ROUTER_USER: str = os.getenv("ROUTER_USER", "admin")
    ROUTER_PASS: str = os.getenv("ROUTER_PASS", "")
    ROUTER_PORT: int = int(os.getenv("ROUTER_PORT", "8728"))

    # Cache
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", ".cache"))

    def __post_init__(self):
        """Validate configuration"""
        if not self.NODE_ID:
            raise ValueError("NODE_ID must be set in .env or environment")
        if not self.API_KEY:
            raise ValueError("API_KEY must be set in .env or environment")

        # Create cache directory if it doesn't exist
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def cache_db_path(self) -> Path:
        """Path to local SQLite cache database"""
        return self.CACHE_DIR / "tickets.db"

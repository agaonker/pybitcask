"""Configuration management for PyBitcask."""

import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, Optional


class BitcaskConfig:
    """Configuration manager for PyBitcask."""

    def __init__(self):
        """Initialize the configuration manager."""
        self.system = platform.system().lower()
        self.config_data: Dict[str, Any] = {}
        self._load_config()

    @property
    def default_data_dir(self) -> Path:
        """Get the platform-specific default data directory."""
        if self.system == "darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "pybitcask"
        elif self.system == "linux":
            return Path("/var/lib/pybitcask")
        elif self.system == "windows":
            return Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData")) / "pybitcask"
        else:
            return Path.home() / ".pybitcask"

    @property
    def config_dir(self) -> Path:
        """Get the platform-specific configuration directory."""
        if self.system == "darwin":  # macOS
            return Path.home() / "Library" / "Preferences" / "pybitcask"
        elif self.system == "linux":
            return Path.home() / ".config" / "pybitcask"
        elif self.system == "windows":
            return Path(os.environ.get("APPDATA", "")) / "pybitcask"
        else:
            return Path.home() / ".pybitcask"

    @property
    def config_file(self) -> Path:
        """Get the path to the configuration file."""
        return self.config_dir / "config.json"

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    self.config_data = json.load(f)
            else:
                self.config_data = {
                    "data_dir": str(self.default_data_dir),
                    "debug_mode": False,
                }
                self._save_config()
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            self.config_data = {
                "data_dir": str(self.default_data_dir),
                "debug_mode": False,
            }

    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                json.dump(self.config_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")

    def get_data_dir(self, override_dir: Optional[str] = None) -> Path:
        """Get the data directory path.

        Args:
        ----
            override_dir: Optional override directory from command line

        Returns:
        -------
            Path object for the data directory

        """
        if override_dir:
            return Path(override_dir)
        return Path(self.config_data.get("data_dir", self.default_data_dir))

    def get_debug_mode(self) -> bool:
        """Get the debug mode setting."""
        return self.config_data.get("debug_mode", False)

    def set_data_dir(self, data_dir: str) -> None:
        """Set the data directory in configuration."""
        self.config_data["data_dir"] = data_dir
        self._save_config()

    def set_debug_mode(self, debug_mode: bool) -> None:
        """Set the debug mode in configuration."""
        self.config_data["debug_mode"] = debug_mode
        self._save_config()


# Global configuration instance
config = BitcaskConfig()

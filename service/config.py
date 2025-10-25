"""Configuration management for Physica service"""

import os
import toml
from pathlib import Path
from typing import Dict, List, Any


class Config:
    """Service configuration"""
    
    DEFAULT_CONFIG = {
        "service": {
            "scan_interval": 5,
            "mount_base": "/media/deck",
            "auto_launch_delay": 2  # Seconds to wait before auto-launching
        },
        "wine": {
            "default_version": "GE-Proton8-14",
            "search_paths": [
                "~/.steam/steam/compatibilitytools.d",
                "/usr/share/steam/compatibilitytools.d"
            ]
        },
        "paths": {
            "cache_dir": "~/.cache/physica",
            "config_dir": "~/.config/physica"
        }
    }
    
    def __init__(self, config_path: str = None):
        """Initialize configuration
        
        Args:
            config_path: Optional path to config file. If None, uses default location.
        """
        if config_path is None:
            config_path = os.path.expanduser("~/.config/physica/config.toml")
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = toml.load(f)
                # Merge with defaults for missing keys
                return self._merge_configs(self.DEFAULT_CONFIG.copy(), config)
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_default_config()
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Recursively merge override config into base config"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._merge_configs(base[key], value)
            else:
                base[key] = value
        return base
    
    def _save_default_config(self):
        """Save default configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                toml.dump(self.DEFAULT_CONFIG, f)
            print(f"Created default config at {self.config_path}")
        except Exception as e:
            print(f"Warning: Failed to save default config: {e}")
    
    @property
    def scan_interval(self) -> int:
        """Seconds between device scans"""
        return self.config["service"]["scan_interval"]
    
    @property
    def mount_base(self) -> str:
        """Base directory where devices are mounted"""
        return self.config["service"]["mount_base"]
    
    @property
    def auto_launch_delay(self) -> int:
        """Seconds to wait before auto-launching inserted cartridge"""
        return self.config["service"]["auto_launch_delay"]
    
    @property
    def default_wine_version(self) -> str:
        """Default Wine/Proton version"""
        return self.config["wine"]["default_version"]
    
    @property
    def wine_search_paths(self) -> List[str]:
        """Paths to search for Wine/Proton installations"""
        return [os.path.expanduser(p) for p in self.config["wine"]["search_paths"]]
    
    @property
    def cache_dir(self) -> Path:
        """Cache directory path"""
        path = Path(os.path.expanduser(self.config["paths"]["cache_dir"]))
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def config_dir(self) -> Path:
        """Config directory path"""
        path = Path(os.path.expanduser(self.config["paths"]["config_dir"]))
        path.mkdir(parents=True, exist_ok=True)
        return path


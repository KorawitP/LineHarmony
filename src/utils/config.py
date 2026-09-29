"""Configuration management system."""

import json
from pathlib import Path
from typing import Any, Dict


class Config:
    """Configuration manager for the layout engine."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to custom config file. If None, uses default.
        """
        self._config: Dict[str, Any] = {}
        self._load_default()
        
        if config_path:
            self._load_custom(config_path)
    
    def _load_default(self):
        """Load default configuration."""
        default_path = Path(__file__).parent.parent.parent / "config" / "default_config.json"
        if default_path.exists():
            with open(default_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
    
    def _load_custom(self, config_path: str):
        """Load and merge custom configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            custom_config = json.load(f)
            self._deep_merge(self._config, custom_config)
    
    def _deep_merge(self, base: dict, update: dict):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'scoring.ratio_weight')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'scoring.ratio_weight')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()


# Global config instance
_global_config = None


def get_config(config_path: str = None) -> Config:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config

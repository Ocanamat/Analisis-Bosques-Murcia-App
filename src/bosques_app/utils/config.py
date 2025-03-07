import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    def __init__(self):
        # Get the directory containing this script
        self.app_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_dir = self.app_dir / 'config'
        
        # Load settings from YAML
        with open(self.config_dir / 'app_settings.yaml', 'r', encoding='utf-8') as f:
            yaml_settings = yaml.safe_load(f)
        
        # Flatten settings for backward compatibility
        self.settings: Dict[str, Any] = {
            'window_title': yaml_settings['window']['title'],
            'plot_background': yaml_settings['plot']['background'],
            'plot_grid_alpha': yaml_settings['plot']['grid_alpha'],
            'default_label_style': yaml_settings['style']['default_label'],
            'frame_margins': tuple(yaml_settings['window']['frame_margins']),
            'tree_column_widths': yaml_settings['tree']['column_widths']
        }
        
    def get(self, key: str) -> Any:
        """Get a configuration value"""
        return self.settings.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self.settings[key] = value
    
    def get_resource_path(self, *paths) -> str:
        """Get the absolute path to a resource file"""
        return str(self.app_dir / 'resources' / Path(*paths))
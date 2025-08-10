"""
Settings configuration for the Binance portfolio management application.
"""
import os
import json
from pathlib import Path

class Settings:
    """Manages application settings and configuration."""
    
    DEFAULT_SETTINGS = {
        'api_key': '',
        'api_secret': '',
        'active_watchlist': 'default',
        'refresh_interval': 5000,  # milliseconds
        'data_directory': 'data',
        'theme': 'default'
    }
    
    def __init__(self):
        """Initialize settings from file or defaults."""
        self.config_dir = Path.home() / '.tradetracker'
        self.config_file = self.config_dir / 'settings.json'
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
        
    def load_settings(self):
        """Load settings from the configuration file."""
        if not self.config_dir.exists():
            os.makedirs(self.config_dir, exist_ok=True)
            
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
                
    def save_settings(self):
        """Save current settings to the configuration file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")
            
    def get(self, key, default=None):
        """Get a setting value by key."""
        return self.settings.get(key, default)
        
    def set(self, key, value):
        """Set a setting value and save to file."""
        self.settings[key] = value
        self.save_settings()
        
    def ensure_data_directory(self):
        """Ensure the data directory exists."""
        data_dir = Path(self.get('data_directory'))
        if not data_dir.is_absolute():
            data_dir = self.config_dir / data_dir
            
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

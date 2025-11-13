import json
import os
from pathlib import Path

class Config:
    def __init__(self, config_file='config.json'):
        self.root_dir = Path(__file__).parent.parent        
        self.config_path = self.root_dir / config_file
        
        if not os.path.exists(self.config_path):
            self._create_default_config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        for section in config_data.values():
            for key, value in section.items():
                setattr(self, key, value)
    
    def _create_default_config(self):
        default_config = {
            "bot": {
                "token": "YOUR_BOT_TOKEN",
            },
            "find": {
                "required_match_score": 0.2,
                "recommendations_count": 20,
            },
            "tags": {
                "ghosts_count": 10,
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as file:
            json.dump(default_config, file, indent=4, ensure_ascii=False)

import logging
from pathlib import Path
from typing import List, Dict

import yaml


class AccountManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.state_dir = Path(self.config.get('state_dir', './data'))
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict:
        with open(config_path) as f:
            return yaml.safe_load(f)

    def get_accounts(self) -> List[Dict]:
        return self.config['accounts']

    def get_state_path(self, account_name: str) -> Path:
        return self.state_dir / f"{account_name}_last_imported.txt"

    async def get_last_imported_id(self, account_name: str) -> int:
        state_file = self.get_state_path(account_name)
        try:
            return int(state_file.read_text())
        except (FileNotFoundError, ValueError):
            return 0

    async def save_last_imported_id(self, account_name: str, game_id: int):
        state_file = self.get_state_path(account_name)

        try:
            state_file.write_text(str(game_id))
            logging.info(f"Wrote {game_id=} to {state_file}")
        except:
            logging.error(f"Failed to write {game_id=} to {state_file}", exc_info=True)
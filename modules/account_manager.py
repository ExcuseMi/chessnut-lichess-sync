import json
import logging
from pathlib import Path
from typing import List

import yaml

from modules.models import AppConfig, AccountConfig, ImportedGame


class AccountManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config : AppConfig = self._load_config(config_path)
        self.state_dir = Path(self.config.state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> AppConfig:
        with open(config_path) as f:
            return AppConfig.model_validate(yaml.safe_load(f))

    def get_accounts(self) -> List[AccountConfig]:
        return self.config.accounts

    def get_state_path(self, account_name: str) -> Path:
        return self.state_dir / f"{account_name}_imported_games.json"

    async def get_imported_games(self, account_name: str) -> List[ImportedGame]:
        state_file = self.get_state_path(account_name)
        try:
            if state_file.exists():
                data = json.loads(state_file.read_text())
                return [ImportedGame(**game) for game in data]
            return []
        except Exception as e:
            logging.error(f"Failed to read imported games from {state_file}", exc_info=True)
            return []

    async def get_last_imported_id(self, imported_games : List[ImportedGame]) -> int:
        """Returns the highest chessnut_game_id from the imported games"""
        if not imported_games:
            return 0

        # Filter out games without chessnut_game_id and get the max ID
        valid_ids = [g.chessnut_game.id for g in imported_games if g.chessnut_game.id is not None]
        return max(valid_ids) if valid_ids else 0

    async def save_imported_game(self, account_name: str, imported_game: ImportedGame):
        state_file = self.get_state_path(account_name)

        # Get existing games
        existing_games = await self.get_imported_games(account_name)

        # Add the new game
        existing_games.append(imported_game)

        # Prepare data for JSON serialization
        games_data = []
        for game in existing_games:
            game_dict = game.dict()
            # Convert datetime to UTC ISO string if it exists
            if game_dict.get('imported_at'):
                game_dict['imported_at'] = game_dict['imported_at'].isoformat()
            games_data.append(game_dict)

        try:
            # Write the updated list to file
            state_file.write_text(json.dumps(games_data, indent=2))
            logging.debug(f"Updated imported games in {state_file}")
        except Exception as e:
            logging.error(f"Failed to write imported games to {state_file}", exc_info=True)
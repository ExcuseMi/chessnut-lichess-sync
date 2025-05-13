import asyncio
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from typing import Dict

from modules import chessnut_api, lichess_api
from modules.account_manager import AccountManager


class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s :: [%(levelname)-5.5s]  %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# ----------------------------------------------------------------------
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
file_handler = TimedRotatingFileHandler("./logs/main.log",
                                   when="midnight",
                                   backupCount=10)


def setup_logging():
    """Configure logging for both Docker and local environments"""

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler (always output to stdout for Docker)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(console_handler)

    # File handler only in non-Docker environments
    file_handler = TimedRotatingFileHandler(
        "logs/main.log",
        when="midnight",
        backupCount=10
    )
    file_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(file_handler)


async def import_games_for_account(account: Dict, account_manager: AccountManager):
    account_name = account['name']
    last_game_id = await account_manager.get_last_imported_id(account_name)

    chessnut_login = await chessnut_api.login(
        account['chessnut']['email'],
        account['chessnut']['password']
    )

    if not chessnut_login:
        logging.warning(f"Failed to login to Chessnut for account {account_name}")
        return False

    logging.info(f"Logged in successfully to Chessnut for account {account_name}")
    chessnut_games = await chessnut_api.get_games(chessnut_login, last_game_id)

    if not chessnut_games:
        logging.info(f"No new games for account {account_name}")
        return True

    logging.info(f"Found {len(chessnut_games)} new games for account {account_name}")

    for game in chessnut_games:
        try:
            pgn = await chessnut_api.get_pgn(game.pgn)
            if not pgn:
                continue

            if await lichess_api.import_game(pgn, account['lichess']['api_key']):
                logging.info(f"Imported game {game.game_id} for account {account_name}")
                await account_manager.save_last_imported_id(account_name, game.game_id)
                await asyncio.sleep(10)
            else:
                logging.error(f"Failed to import game {game.game_id} for account {account_name}")
                return False
        except Exception as e:
            logging.error(f"Error importing game {game.game_id} for account {account_name}", exc_info=e)
            return False

    return True


async def main():
    account_manager = AccountManager()

    while True:
        for account in account_manager.get_accounts():
            try:
                await import_games_for_account(account, account_manager)
                interval = account.get('interval_minutes', 1) * 60
                await asyncio.sleep(interval)
            except Exception as e:
                logging.error(f"Error processing account {account['name']}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retrying


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
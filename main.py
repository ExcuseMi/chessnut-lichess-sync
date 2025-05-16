import asyncio
import datetime
import logging
import sys
from typing import Optional, List, Union

from modules import chessnut_api, lichess_api
from modules.account_manager import AccountManager, ImportedGame, AccountConfig
from modules.lichess_api import LichessGameReference
from modules.models import ChessnutGameReference, ChessnutGame

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


def setup_logging():
    """Configure logging for Docker (stdout only)"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(console_handler)
async def import_games_for_account(account: AccountConfig, account_manager: AccountManager):
    account_name = account.name
    imported_games : List[ImportedGame] = await account_manager.get_imported_games(account_name)
    last_game_id = await account_manager.get_last_imported_id(imported_games)

    chessnut_login = await chessnut_api.login(account.chessnut)
    if not chessnut_login:
        logging.warning(f"Failed to login to Chessnut for account {account_name}")
        return False

    logging.info(f"Logged in successfully to Chessnut for account {account_name}")
    chessnut_games_reference: Optional[List[ChessnutGameReference]] = await chessnut_api.get_games(chessnut_login, last_game_id)

    if not chessnut_games_reference:
        logging.info(f"No new games for account {account_name}")
        return True

    logging.info(f"Found {len(chessnut_games_reference)} new games for account {account_name}")
    for chessnut_game_reference in chessnut_games_reference:
        try:
            pgn = await chessnut_api.get_pgn(chessnut_game_reference.pgn_url)
            if not pgn:
                logging.warning(f"Failed to retrieve pgn for {chessnut_game_reference.pgn_url}")
                continue

            lichess_game_reference : Union[str, LichessGameReference] = await lichess_api.import_game(pgn, account.lichess.api_key)
            chessnut_game: ChessnutGame = ChessnutGame(id=chessnut_game_reference.id, pgn=pgn)

            if isinstance(lichess_game_reference, LichessGameReference):
                logging.info(f"Imported chessnut_game {chessnut_game_reference.id} for account {account_name} into lichess: lichess game id {lichess_game_reference.id}, lichess url: {lichess_game_reference.url}")
                imported_game = ImportedGame(chessnut_game=chessnut_game, lichess_game=lichess_game_reference, imported_at=datetime.datetime.now(datetime.UTC))
                await account_manager.save_imported_game(account_name, imported_game)
                await asyncio.sleep(10)
            elif lichess_game_reference:
                imported_game = ImportedGame(chessnut_game=chessnut_game, lichess_game=None, imported_at=datetime.datetime.now(datetime.UTC), error=lichess_game_reference)
                await account_manager.save_imported_game(account_name, imported_game)
                logging.error(f"Failed to import chessnut_game {chessnut_game_reference.id} for account {account_name}")
            else:
                logging.error(f"Failed to import chessnut_game {chessnut_game_reference.id} for account {account_name} without error")

        except Exception as e:
            logging.error(f"Error importing chessnut_game {chessnut_game_reference.id} for account {account_name}", exc_info=e)
            return False

    return True


async def main():
    account_manager = AccountManager()
    accounts = account_manager.get_accounts()
    if not accounts:
        logging.warning("No accounts are configured!")
        return

    # Create and gather all tasks
    tasks = [asyncio.create_task(loop_account(account, account_manager))
             for account in accounts]

    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.error("Main error", exc_info=True)
    finally:
        # Cancel all tasks if we exit
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def loop_account(account, account_manager):
    interval = account.interval_minutes * 60
    while True:
        try:
            await import_games_for_account(account, account_manager)
        except Exception as e:
            logging.error(f"Error processing account {account.name}", exc_info=True)
        finally:
            await asyncio.sleep(interval)


if __name__ == "__main__":
    setup_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    except Exception as e:
        logging.error("Fatal error", exc_info=True)
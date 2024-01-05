import asyncio
import logging
import os

from dotenv import load_dotenv

import chessnut_api
import lichess_api

last_imported_file_name = "last-imported.txt"
load_dotenv()  # take environment variables from .env.
from logging.handlers import TimedRotatingFileHandler
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
file_handler = TimedRotatingFileHandler("main.log",
                                   when="midnight",
                                   backupCount=10)

async def get_last_imported_file_id() -> int:
    try:
        with open(last_imported_file_name, "r") as file:
            return int(file.read())
    except:
        return 0


async def save_last_imported_file_id(game_id: int):
    with open(last_imported_file_name, "w") as file:
        file.write(str(game_id))


async def import_games():
    last_game_id = await get_last_imported_file_id()
    chessnut_login = await chessnut_api.login()
    if chessnut_login:
        logging.info(f"Logged in successfully to chessnut.")
        all_pgns = []
        chessnut_games = await chessnut_api.get_games(chessnut_login, all_pgns, last_game_id)
        if chessnut_games:
            logging.info(f"Found {len(chessnut_games)} new games")
            for game in chessnut_games:
                try:
                    pgn = await chessnut_api.get_pgn(game.pgn)
                    if pgn:
                        if await lichess_api.import_game(pgn):
                            logging.info(f"Imported game {game}")
                            await save_last_imported_file_id(game.id)
                            await asyncio.sleep(10)
                        else:
                            return
                            
                    else:
                        return
                except Exception as e:
                    logging.error(f"fError while importing game {game.id}", exc_info=e)
                    return
        else:
            logging.info("No new games...")
    else:
        logging.warning("Failed to login to chessnut!")

async def main():
    while True:
        try:
            await import_games()
        except Exception as e:
            logging.error("Error while importing games", exc_info=e)
        await asyncio.sleep(int(os.getenv("interval-minutes")) * 60)


if __name__ == "__main__":
    import time

    s = time.perf_counter()
    asyncio.run(main())

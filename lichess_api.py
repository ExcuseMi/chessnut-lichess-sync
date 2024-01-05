import logging
import os

import aiohttp

LICHESS_GAME_IMPORT_URI = "https://lichess.org/api/import"

async def import_game(pgn: str):
    async with aiohttp.ClientSession() as session:
        headers = {'Authorization': f"Bearer {os.getenv('lichess-personal-key')}"}
        form_data = aiohttp.FormData()
        form_data.add_field("pgn", pgn)

        async with session.post(LICHESS_GAME_IMPORT_URI, headers=headers, data=form_data) as r:
            if r.status == 200:
                result = await r.json()
                logging.info(f"Imported game: {result}")
                return result
            elif r.status == 400:
                logging.warning(f"Importing game failed with status code {r.status} but assuming it's just duplicate")
                return True

            else:
                logging.warning(f"Importing game failed with status code {r.status}")
                return False

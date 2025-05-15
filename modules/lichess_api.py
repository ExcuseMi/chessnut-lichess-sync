import logging
from typing import Optional, Dict

import aiohttp

from modules.models import LichessGameReference

LICHESS_GAME_IMPORT_URI = "https://lichess.org/api/import"
LICHESS_GAME_IMPORT_EXPORT_URI = "https://lichess.org/api/games/export/imports"


async def import_game(
        pgn: str,
        api_key: str,
        session: Optional[aiohttp.ClientSession] = None
) -> Optional[LichessGameReference] | Dict[str, any]:
    """
    Import a PGN game to Lichess.

    Args:
        pgn: The PGN string to import
        api_key: Lichess API key for authentication
        session: Optional existing aiohttp session

    Returns:
        The imported game data if successful, None otherwise
        Returns True for duplicate games (400 status)
    """
    headers = {'Authorization': f"Bearer {api_key}"}
    form_data = aiohttp.FormData()
    form_data.add_field("pgn", pgn)

    try:
        async def _import(session):
            async with session.post(
                    LICHESS_GAME_IMPORT_URI,
                    headers=headers,
                    data=form_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return LichessGameReference.model_validate(result)
                elif response.status == 400:
                    # Handle duplicate games gracefully
                    error = await response.json()
                    if "This game already exists" in error:
                        logging.info("Game already exists on Lichess (duplicate)")
                        return True
                    error_message = error.get('error', {})
                    logging.warning(f"Bad request when importing game: {error_message}")
                    return error_message
                elif response.status == 429:
                    logging.warning("Rate limit exceeded for Lichess API")
                    return None
                elif response.status == 401:
                    logging.warning("Unauthorized - invalid Lichess API key")
                    return None
                else:
                    logging.warning(
                        f"Failed to import game. Status: {response.status}, Response: {await response.text()}"
                    )
                    return None

        if session:
            return await _import(session)
        else:
            async with aiohttp.ClientSession() as new_session:
                return await _import(new_session)

    except aiohttp.ClientError as e:
        logging.error(f"Network error while importing game to Lichess: {str(e)}")
        return None
    except Exception as e:
        logging.error("Unexpected error while importing game to Lichess", exc_info=True)
        return None
async def export_pgns(
        api_key: str,
        session: Optional[aiohttp.ClientSession] = None
) -> Optional[str]:

    headers = {'Authorization': f"Bearer {api_key}"}

    try:
        async def _export(session):
            async with session.get(
                    LICHESS_GAME_IMPORT_EXPORT_URI,
                    headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.text()
                    return result
                elif response.status == 400:
                    # Handle duplicate games gracefully
                    error = await response.text()
                    if "This game already exists" in error:
                        logging.info("Game already exists on Lichess (duplicate)")
                        return True
                    logging.warning(f"Bad request when exporting games: {error}")
                    return None
                elif response.status == 429:
                    logging.warning("Rate limit exceeded for Lichess API")
                    return None
                elif response.status == 401:
                    logging.warning("Unauthorized - invalid Lichess API key")
                    return None
                else:
                    logging.warning(
                        f"Failed to export games. Status: {response.status}, Response: {await response.text()}"
                    )
                    return None

        if session:
            return await _export(session)
        else:
            async with aiohttp.ClientSession() as new_session:
                return await _export(new_session)

    except aiohttp.ClientError as e:
        logging.error(f"Network error while exporting from Lichess: {str(e)}")
        return None
    except Exception as e:
        logging.error("Unexpected error while exporting from Lichess", exc_info=True)
        return None
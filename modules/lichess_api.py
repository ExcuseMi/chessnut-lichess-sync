import logging
from typing import Optional, Dict, Any

import aiohttp

LICHESS_GAME_IMPORT_URI = "https://lichess.org/api/import"


async def import_game(
        pgn: str,
        api_key: str,
        session: Optional[aiohttp.ClientSession] = None
) -> Optional[Dict[str, Any]]:
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
                    logging.info(f"Successfully imported game: {result.get('id', 'unknown')}")
                    return result
                elif response.status == 400:
                    # Handle duplicate games gracefully
                    error = await response.text()
                    if "This game already exists" in error:
                        logging.info("Game already exists on Lichess (duplicate)")
                        return True
                    logging.warning(f"Bad request when importing game: {error}")
                    return None
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
import hashlib
import json
import logging
from typing import List, Optional

import aiohttp

from modules.models import ChessnutGame, ChessnutAccount, ChessnutGameReference

LOGIN_URI = "https://api.chessnutech.com/api/login"
PNG_LIST_URI = "https://api.chessnutech.com/api/getPgnList"


class ChessnutLogin:
    def __init__(self, token: str, user_id: str):
        self.token = token
        self.user_id = user_id




def convert_password(password: str) -> str:
    """Hash password using SHA-256 as required by Chessnut API."""
    h = hashlib.new('sha256')
    h.update(str.encode(password))
    return h.hexdigest().upper()


async def login(chessnut_account: ChessnutAccount) -> Optional[ChessnutLogin]:
    """
    Authenticate with Chessnut API.

    Returns:
        ChessnutLogin object if successful, None otherwise
        :param chessnut_account:
    """
    encrypted_password = convert_password(chessnut_account.password)
    form_data = aiohttp.FormData()
    form_data.add_field("account", chessnut_account.email)
    form_data.add_field("password", encrypted_password)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(LOGIN_URI, data=form_data) as response:
                result = await response.text()
                json_result = json.loads(result)

                if response.status != 200:
                    logging.error(f"Login failed with status {response.status}: {json_result}")
                    return None

                if json_result.get('code') == 200:
                    data = json_result.get('data', {})
                    return ChessnutLogin(data.get('token'), data.get('user_id'))
                else:
                    logging.error(f"Login failed: {json_result.get('message', 'Unknown error')}")
                    return None
    except Exception as e:
        logging.error("Error during Chessnut login", exc_info=True)
        return None


async def get_games(
        chessnut_login: ChessnutLogin,
        last_game_id: int,
        page: int = 1,
        session: Optional[aiohttp.ClientSession] = None
) -> List[ChessnutGameReference]:
    """
    Fetch games from Chessnut API with pagination support.

    Args:
        chessnut_login: Authenticated session
        last_game_id: Only return games with ID > this value
        page: Current page number
        session: Optional existing aiohttp session

    Returns:
        List of ChessnutGame objects
    """
    form_data = aiohttp.FormData()
    form_data.add_field("token", chessnut_login.token)
    form_data.add_field("user_id", chessnut_login.user_id)
    form_data.add_field("page", str(page))

    try:
        async def _fetch(session):
            async with session.post(PNG_LIST_URI, data=form_data) as response:
                if response.status != 200:
                    text = await response.text()
                    logging.error(f"Failed to fetch games: {text}")
                    return []
                text = await response.text()
                result = json.loads(text)
                if result.get('code') != 200:
                    logging.error(f"API error: {result.get('message', 'Unknown error')}")
                    return []

                data = result.get('data', {})
                pgn_list = data.get('pgnList', [])
                total_pages = data.get('total_page', 1)

                current_page_games = [
                    ChessnutGameReference(id=p['id'], pgn_url=p['pgn'])
                    for p in pgn_list
                    if p['id'] > last_game_id
                ]

                # If we got a full page and there are more pages, fetch next page
                if len(pgn_list) == len(current_page_games) and page < total_pages:
                    next_page_games = await get_games(
                        chessnut_login, last_game_id, page + 1, session
                    )
                    current_page_games.extend(next_page_games)

                return sorted(current_page_games, key=lambda l: l.id, reverse=False)

        if session:
            return await _fetch(session)
        else:
            async with aiohttp.ClientSession() as new_session:
                return await _fetch(new_session)

    except Exception as e:
        logging.error("Error fetching games from Chessnut", exc_info=True)
        return []


async def get_pgn(url: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    """
    Fetch PGN content from a URL.

    Args:
        url: PGN URL to fetch
        session: Optional existing aiohttp session

    Returns:
        PGN content as string or None if failed
    """
    try:
        async def _fetch(session):
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                logging.error(f"Failed to fetch PGN from {url}: HTTP {response.status}")
                return None

        if session:
            return await _fetch(session)
        else:
            async with aiohttp.ClientSession() as new_session:
                return await _fetch(new_session)

    except Exception as e:
        logging.error(f"Error fetching PGN from {url}", exc_info=True)
        return None
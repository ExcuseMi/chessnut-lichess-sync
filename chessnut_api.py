import hashlib
import json
import os

import aiohttp as aiohttp

LOGIN_URI = "https://api.chessnutech.com/api/login"
PNG_LIST_URI = "https://api.chessnutech.com/api/getPgnList"


def convert_password(password):
    h = hashlib.new('sha256')
    h.update(str.encode(password))
    return h.hexdigest().upper()


class ChessnutLogin:
    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id


class ChessnutGame:
    def __init__(self, id, pgn):
        self.id = id
        self.pgn = pgn

    def __repr__(self):
        return f"{self.id} -> {self.pgn}"


async def login() -> ChessnutLogin:
    username = os.getenv("chessnut-username")
    encrypted_password = convert_password(os.getenv("chessnut-password"))
    form_data = aiohttp.FormData()
    form_data.add_field("account", username)
    form_data.add_field("password", encrypted_password)

    async with aiohttp.ClientSession() as session:
        async with session.post(LOGIN_URI, data=form_data) as r:
            result = await r.text()
            json_result = json.loads(result)
            code = json_result.get('code', None)
            if code == 200:
                data = json_result.get('data')
                return ChessnutLogin(data.get('token'), data.get('user_id'))


async def get_games(chessnut_login: ChessnutLogin, game_urls, last_game_id: int, page: int = 1) -> [ChessnutGame]:
    form_data = aiohttp.FormData()
    form_data.add_field("token", chessnut_login.token)
    form_data.add_field("user_id", chessnut_login.user_id)
    form_data.add_field("page", page)

    async with aiohttp.ClientSession() as session:
        async with session.post(PNG_LIST_URI, data=form_data) as r:
            result = await r.text()
            json_result = json.loads(result)
            code = json_result.get('code', None)
            if code == 200:
                data = json_result.get('data')
                if data:
                    total_pages = data.get('total_page', 1)

                    pgn_list = data.get('pgnList', [])
                    all_pgns = game_urls if game_urls else []
                    new_pgns = list(
                        map(lambda p: ChessnutGame(p.get('id'), p.get('pgn')), filter(lambda p: p.get('id'), pgn_list)))
                    all_pgns.extend(new_pgns)
                    if len(new_pgns) == len(pgn_list) and total_pages > page:
                        return await get_games(chessnut_login, all_pgns, last_game_id, page + 1)
                    else:
                        return sorted(all_pgns, key=lambda p: p.id, reverse=False)


async def get_pgn(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                return await r.text()

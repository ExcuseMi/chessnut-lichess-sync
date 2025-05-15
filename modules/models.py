from datetime import datetime
from typing import Optional, List, Dict

from pydantic import BaseModel, EmailStr


class LichessGameReference(BaseModel):
    id : Optional[str] = None
    url : Optional[str] = None
class ChessnutGame(BaseModel):
    id: int
    pgn : str

    def __repr__(self):
        return f"ChessnutGame(id={self.id}, pgn={self.pgn[:20]}...)" if self.pgn else f"ChessnutGame(id={self.id})"
class ChessnutGameReference(BaseModel):
    id: int
    pgn_url : str

    def __repr__(self):
        return f"ChessnutGame(id={self.id}, pgn_url={self.pgn_url[:20]}...)" if self.pgn else f"ChessnutGame(id={self.id})"
class ChessnutAccount(BaseModel):
    email: EmailStr
    password: str

class LichessAccount(BaseModel):
    api_key: str

class AccountConfig(BaseModel):
    name: str
    chessnut: ChessnutAccount
    lichess: LichessAccount
    interval_minutes: int = 60

class AppConfig(BaseModel):
    accounts: List[AccountConfig]
    state_dir: str = "/app/data"
class ImportedGame(BaseModel):
    chessnut_game: Optional[ChessnutGame] = None
    lichess_game: Optional[LichessGameReference] = None
    imported_at: Optional[datetime] = None
    error: Optional[Dict] = None
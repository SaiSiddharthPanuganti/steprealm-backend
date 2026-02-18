from pydantic import BaseModel


class ClaimTileRequest(BaseModel):
    q: int
    r: int

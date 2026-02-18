from pydantic import BaseModel, Field


class ClaimTileRequest(BaseModel):
    q: int
    r: int


class ClaimByLocationRequest(BaseModel):
    latitude: float = Field(ge=-85.0, le=85.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    distance_m: float = Field(ge=0.0, le=200.0)

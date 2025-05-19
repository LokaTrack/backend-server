from pydantic import BaseModel, Field

class SocketModel(BaseModel):
    trackerId: str = Field(..., alias="id")
    location: {
        location: float;
        latitude: float;
    }

class SocketLocationModel(BaseModel):

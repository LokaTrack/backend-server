from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

class GPSDataModel(BaseModel):
    id: str
    lat: float
    long: float
    satellites: Optional[int] = None
    timestamp: str
    class Config:
        json_schema_extra = {
            "example": {
                "id": "CC:DB:A7:9B:7A:10",
                "lat": -11.262273333,
                "long": 11.0032413,
                "satellites": 99,
            }
        }
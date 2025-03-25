from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
from enum import Enum

class deliveryStatusEnum(str, Enum):
    delivery = "in transit"
    checkIn = "arrived"
    checkOut = "delivered"
    returnToSender = "returned"  

# package model
class packageModel(BaseModel):
    packageId: str
    recipientName : str
    recipientNumber: int
    recipientAddress: str
    
    packageWeight: float
    
    packageDimension: dict = Field(
        default_factory=lambda: {
            "length": 0.0, 
            "width": 0.0, 
            "height": 0.0
            })
    additionalNotes: Optional[str] = None
    

# package delivery model
class packageDeliveryModel(BaseModel):
    packageId: str
    driverId: str
    deliveryStatus: deliveryStatusEnum
    trackerId: Optional[str] = None
    
    deliveryStartTime: datetime 
    deliveryStartLocation: dict = Field(
        default_factory=lambda: {
            "latitude": 0.0, 
            "longitude": 0.0
            })
    
    checkInTime: Optional[datetime] = None
    checkInLocation: dict = Field(
        default_factory=lambda: {
            "latitude": 0.0, 
            "longitude": 0.0
            })
    
    checkOutTime: Optional[datetime] = None
    checkOutLocation: dict = Field(
        default_factory=lambda: {
            "latitude": 0.0, 
            "longitude": 0.0
            })


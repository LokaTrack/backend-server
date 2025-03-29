from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class deliveryStatusEnum(str, Enum):
    delivery = "dikirim"
    checkin = "sampai"
    checkout = "selesai"
    returned = "dikembalikan"  

# package delivery model
class packageDeliveryModel(BaseModel):
    orderNo: str
    driverId: Optional [str] = None
    customer: Optional [str] = None
    address: Optional [str] = None
    totalWeight: Optional [float] = 0
    totalPrice: Optional [float] = 0
    deliveryStatus: deliveryStatusEnum = deliveryStatusEnum.delivery
    trackerId: Optional[str] = "Ue2KlB6IMPdfoBN4CR2b"    
    deliveryStartTime: datetime = Field(default_factory=datetime.now)
    checkInTime: Optional[datetime] = None
    checkOutTime: Optional[datetime] = None
    lastUpdateTime: datetime = Field(default_factory=datetime.now)
    
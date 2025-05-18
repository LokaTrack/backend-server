from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class deliveryStatusEnum(str, Enum):
    delivery = "On Delivery"
    checkin = "Check-in"
    checkout = "Check-out"
    returned = "Return"  

# package delivery model
class packageDeliveryModel(BaseModel):
    orderNo: str
    driverId: Optional [str] = None
    customer: Optional [str] = None
    address: Optional [str] = None
    itemsList: Optional [list] = None
    totalWeight: Optional [float] = 0
    totalPrice: Optional [float] = 0
    deliveryStatus: deliveryStatusEnum = deliveryStatusEnum.delivery
    trackerId: Optional[str] = "CC:DB:A7:9B:7A:00"    
    deliveryStartTime: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checkInTime: Optional[datetime] = None
    checkOutTime: Optional[datetime] = None
    lastUpdateTime: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class returnItemsModel(BaseModel):
    unitName: str
    weight: float
    quantity: int
    unitMetrics: str
    unitPrice: float
    total: float

class packageDeliveryReturnModel(BaseModel):
    orderNo: str
    returnId: Optional [str] = None
    deliveryOrderImages: Optional [list] = None
    returnDate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    returnedItems: Optional [list] = None
    totalWeight: Optional [float] = 0
    totalPrice: Optional [float] = 0
    totalItems: Optional [int] = 0
    reason: Optional [str] = None

class updateDeliveryStatusModel(BaseModel):
    orderNo: str
    deliveryStatus: deliveryStatusEnum 
    checkInTime: Optional[datetime] = None
    checkOutTime: Optional[datetime] = None
    lastUpdateTime: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
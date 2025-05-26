from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

# Order item model
class orderItemModel(BaseModel):
    name: str
    quantity: float
    unitPrice: float
    total: float
    weight: float = 0.0  
    unitMetrics: str  
    type: str   # Type of product, e.g., "HYDROPONIC", "ORGANIC", etc.


    @field_validator('total')
    @classmethod
    def validate_total(cls, total, values):
        # Check if quantity and unitPrice are available
        if 'quantity' in values.data and 'unitPrice' in values.data:
            quantity = values.data['quantity']
            unit_price = values.data['unitPrice']
            expected_total = quantity * unit_price
            
            # Allow small floating point differences (0.01)
            if abs(total - expected_total) > 0.01:
                raise ValueError(f"Total ({total}) doesn't match quantity * unitPrice ({expected_total})")
        return total

# Package order model
class packageOrderModel(BaseModel):
    orderNo: str
    orderId : str
    invoiceNo: str
    invoiceDueAt : Optional [datetime]
    orderDate: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    customer: str
    costomerType : Optional[str] 
    address: str
    addressMapUrl: Optional[str] = None
    phone: str
    items: List[orderItemModel]
    totalWeight: float = 0.0  
    subTotal: float
    discount: float = 0
    shipping: float = 0
    totalPrice: float
    paymentStatus: Optional[str] 
    orderNotes: Optional[str] = ""
    
    @field_validator('subTotal')
    @classmethod
    def validate_subtotal(cls, subtotal, values):
        if 'items' in values.data:
            items = values.data['items']
            expected_subtotal = sum(item.total for item in items)
            
            # Allow small floating point differences (0.01)
            if abs(subtotal - expected_subtotal) > 0.01:
                raise ValueError(f"subTotal ({subtotal}) doesn't match sum of item totals ({expected_subtotal})")
        return subtotal

    @field_validator('totalWeight')
    @classmethod
    def validate_total_weight(cls, total_weight, values):
        if 'items' in values.data:
            items = values.data['items']
            expected_weight = sum(item.weight * item.quantity for item in items)
            
            # Allow small floating point differences (0.001 for weight in kg)
            if abs(total_weight - expected_weight) > 0.001:
                raise ValueError(f"totalWeight ({total_weight}) doesn't match sum of item weights ({expected_weight})")
        return total_weight

    @field_validator('totalPrice')
    @classmethod
    def validate_total(cls, totalPrice, values):
        if all(field in values.data for field in ['subTotal', 'discount', 'shipping']):
            subtotal = values.data['subTotal']
            discount = values.data['discount']
            shipping = values.data['shipping']
            
            expected_total = subtotal - discount + shipping
            
            # Allow small floating point differences (0.01)
            if abs(totalPrice - expected_total) > 0.01:
                raise ValueError(f"total price({totalPrice}) doesn't match subTotal - discount + shipping ({expected_total})")
        return totalPrice   
    
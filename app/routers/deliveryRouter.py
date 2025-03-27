from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models.deliveryModel import packageDeliveryModel
from app.services.deliveryService import startDeliveryPackage 
from app.utils.auth import get_current_user


router = APIRouter(prefix="/api/v1/delivery", tags=["Delivery"])


@router.post("/start", status_code=201)
async def startDeliveryRouter(deliveryDataInput: packageDeliveryModel, currentUser: dict = Depends(get_current_user)):
    """Add a New Package to Delivery Collection"""
    try:
        result = await startDeliveryPackage(deliveryDataInput, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )
    
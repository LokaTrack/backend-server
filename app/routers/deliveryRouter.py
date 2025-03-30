from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models.deliveryModel import packageDeliveryModel, updateDeliveryStatusModel
from app.services.deliveryService import startDeliveryPackage, updateDeliveryStatus, getPackageDeliveryById, getAllPackageDelivery
from app.utils.auth import get_current_user


router = APIRouter(prefix="/api/v1", tags=["Delivery"])


@router.post("/delivery/start", status_code=201)
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
    

@router.put("/delivery", status_code=201)
async def updateDeliveryRouter(deliveryDataInput:updateDeliveryStatusModel, currentUser: dict = Depends(get_current_user)):
    """Update Delivery Status"""
    try:
        result = await updateDeliveryStatus(deliveryDataInput, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )
    
@router.get("/delivery/{orderNo}", status_code=200)
async def getPackageRouter(
    orderNo: str,
    currentUser: dict = Depends(get_current_user)
    ):
    """Get Package Delivery Detail ID"""
    try:
        result = await getPackageDeliveryById(orderNo)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )

@router.get("/delivery/all/delivery", status_code=200)
async def getAllPackageRouter ():
    """Get All Package Delivery"""
    try:
        result = await getAllPackageDelivery()
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )
import json
from typing import List
from fastapi import APIRouter, File, HTTPException, Depends, UploadFile, Form
from fastapi.responses import JSONResponse
from app.models.deliveryModel import packageDeliveryModel, updateDeliveryStatusModel
from app.services.deliveryService import startDeliveryPackage, updateDeliveryStatus, getPackageDeliveryById, updateDeliveryStatusReturn,getPackageReturnById
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Delivery"])

@router.post("/delivery", status_code=201)
async def start_delivery(deliveryDataInput: packageDeliveryModel, currentUser: dict = Depends(get_current_user)):
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
async def update_delivery_status(deliveryDataInput:updateDeliveryStatusModel, currentUser: dict = Depends(get_current_user)):
    """Update Delivery Status"""
    try:
        result = await updateDeliveryStatus(deliveryDataInput, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )

@router.get("/delivery/return/{orderNo}", status_code=200)
async def get_return_delivery(
    orderNo: str,
    currentUser: dict = Depends(get_current_user)
    ):
    """Get Package Delivery Return ID"""
    try:
        result = await getPackageReturnById(orderNo, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )

@router.post("/delivery/return", status_code=201)
async def return_delivery(
    images: List[UploadFile] = File(...),
    orderNo: str = Form(...),
    returnItems: str = Form(...),
    reason: str = Form(...),
    currentUser: dict = Depends(get_current_user)):
    """Return Delivery"""
    try:
        # Parse items from JSON string back to Python list
        items_list = json.loads(returnItems)
        #  [{"name": "Cabai Merah", "quantity": 7}, {"name": "Apel Fuji", "quantity": 4}]

        result = await updateDeliveryStatusReturn(images, orderNo, items_list, reason, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )
    
@router.get("/delivery/{orderNo}", status_code=200)
async def get_delivery_detail(
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
async def get_all_package():
    """Get All Package Delivery"""
    try:
        result = await getAllPackageDelivery()
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )
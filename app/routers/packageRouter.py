from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.packageModel import packageModel, packageDeliveryModel
from app.services.packageService import addPackage, startDeliveryPackage, getAllPackages

router = APIRouter(prefix="/api/v1", tags=["Package"])

@router.post("/package/add", status_code=201)
async def addPackageRouter(packageDataInput: packageModel):
    """Add a New Package to Package Collection"""
    try:
        result = await addPackage(packageDataInput)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.post("/package/start", status_code=201)
async def startDeliveryRouter(packageDataInput: packageDeliveryModel):
    """Add a New Package to Delivery Collection"""
    try:
        result = await startDeliveryPackage(packageDataInput)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )
    
@router.get("/packages", status_code=200)
async def getAllPackageRouter():
    """Get All Packages"""
    try:
        result = await getAllPackages()
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
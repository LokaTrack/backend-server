from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models.packageModel import packageOrderModel
from app.services.packageService import addPackage, getPackageDetail, getAllPackages
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/package", tags=["Package"])

@router.post("/add", status_code=201)
async def addPackageRouter(
    packageDataInput: packageOrderModel,  
    curentUser: dict = Depends(get_current_user)
    ):
    """Add a New Package to Package Collection"""
    try:
        result = await addPackage(packageDataInput, curentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

    
@router.get("/detail", status_code=200)
async def getPackageRouter(orderNo: str, curentUser: dict = Depends(get_current_user)):
    """Get a Package"""
    try:
        result = await getPackageDetail(orderNo)
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
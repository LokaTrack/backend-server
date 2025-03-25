from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models.packageModel import packageModel, packageDeliveryModel
from app.services.packageService import addPackageDUMMY, startDeliveryPackageDUMMY

router = APIRouter(prefix="/api/v1", tags=["Package Dummy"])

@router.post("/package/add-dummy", status_code=201)
async def addPackageRouterDum():
    """Add a New Package to Package Collection"""
    try:
        result = await addPackageDUMMY()
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.post("/package/start-dummy", status_code=201)
async def startDeliveryRouter(packageId):
    """Add a New Package to Delivery Collection"""
    try:
        result = await startDeliveryPackageDUMMY(packageId)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
       )

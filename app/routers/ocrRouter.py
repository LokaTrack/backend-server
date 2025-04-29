from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.services.ocrService import getItemsData, getOrderNo, getReturnItems


# Assuming you might want to protect these endpoints later
# from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/ocr",
    tags=["OCR"],
    # dependencies=[Depends(get_current_user)] # Uncomment to protect all endpoints in this router
)

@router.post("/order-no")
async def ocr_get_order_no(file: UploadFile = File(...)):
    """ Uploads an image file and extracts the Order No using OCR. """
    try:
        result = await getOrderNo(file)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )


@router.post("/")
async def get_all_items(files: List[UploadFile] = File(...)):
    """Uploads one or more image files and extracts item data using OCR."""
    try:
        result = await getItemsData(files)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.post("/return-item")
async def get_return_items_only(files: List[UploadFile] = File(...)):
    """Uploads one or more image files and extracts return item data using OCR."""
    try:
        result = await getReturnItems(files)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
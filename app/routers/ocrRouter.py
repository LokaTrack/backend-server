from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.services.ocrService import getItemsData, getOrderNo, getReturnItems, scanBarcode


# Assuming you might want to protect these endpoints later
# from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/ocr",
    tags=["OCR"],
    # dependencies=[Depends(get_current_user)] # Uncomment to protect all endpoints in this router
)

@router.post("/")
async def get_all_items(images: List[UploadFile] = File(...)):
    """Uploads one or more image files and extracts item data using OCR."""
    try:
        result = await getItemsData(images)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.post("/order-no")
async def ocr_get_order_no(image: UploadFile = File(...)):
    """ Uploads an image file and extracts the Order No using OCR. """
    try:
        result = await getOrderNo(image)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )

@router.post("/return-item")
async def get_return_items_only(images: List[UploadFile] = File(...)):
    """Uploads one or more image files and extracts return item data using OCR."""
    try:
        result = await getReturnItems(images)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
@router.post("/scan-barcode")
async def scan_barcode(image: UploadFile = File(...)):
    """Uploads an image file and scans it for QR codes or barcodes."""
    try:
        result = await scanBarcode(image)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
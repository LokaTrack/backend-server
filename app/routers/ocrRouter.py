from fastapi import APIRouter, Body, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from typing import List
from app.services.ocrService import getItemsData, getOrderNo, getReturnItems, scanBarcode, getOrderNoFromURL, getReturnItemsPaddle, getReturnItemPaddleUsingDatabase
from app.utils.auth import get_current_user

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

# @router.post("/order-no")
# async def ocr_get_order_no(image: UploadFile = File(...)):
#     """ Uploads an image file and extracts the Order No using OCR. """
#     try:
#         result = await getOrderNo(image)
#         return result
#     except HTTPException as e:
#         return JSONResponse(
#             status_code=e.status_code,
#             content=e.detail
#         )

@router.post("/return-item")
async def get_return_items_only(
    images: List[UploadFile] = File(...),
    # orderNo : str = Form (..., description="Order No for the return item", example="OB/01-2025/19129"),
    ):
    """Uploads one or more image files and extracts return item data using OCR."""
    try:
        result = await getReturnItemsPaddle(images)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
@router.post("/return-item-db")
async def get_return_items_only(
    images: List[UploadFile] = File(...),
    orderNo : str = Form (..., description="Order No for the return item", example="OB/03-2025/193"),
    ):
    """Uploads one or more image files and extracts return item data using OCR."""
    try:
        result = await getReturnItemPaddleUsingDatabase(images, orderNo)
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

@router.post("/order-no")
async def ocr_get_order_no_from_url(
    url: str = Body(..., embed=True, description="URL containing the Order No"),
    currentUser: dict = Depends(get_current_user)
    ):
    """Extracts the Order No from a given URL."""
    try:
        result = await getOrderNoFromURL(url, currentUser)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
    
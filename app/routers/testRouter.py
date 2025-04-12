from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from typing import Dict, Union, Any, Optional
import os
from app.utils.compress import compress_image

router = APIRouter(prefix="/api/v1/demo", tags=["Demo Router"])

@router.post("/compress-images")
async def compress_image_test(
    file: UploadFile = File(...),
    quality: int = Form(75),  # Default quality is 75%
    resize_width: Optional [int] = Form(None),  # Optional width for resizing
    resize_height: Optional [int] = Form(None),  # Optional height for resizing
    max_size_kb: Optional [int] = Form(None),  # Target maximum size in KB
    is_lossless: Optional [bool] = Form(False),  # Lossless compression (png)
    return_buffer: Optional [bool] = Form(False),  # Return buffer image for stored in storage bucket
    return_image: Optional [bool] = Form(True)  # Whether to return image directly
):
    """Image Compression by VIPS"""
    try:    
        result = await compress_image(
            file, 
            quality=quality, 
            resize_width=resize_width, 
            resize_height=resize_height, 
            max_size_kb=max_size_kb, 
            is_lossless=is_lossless,
            return_buffer=return_buffer, 
            return_image=return_image)
        return result
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=e.detail
        )
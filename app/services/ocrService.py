import os
import re
import pytesseract
from PIL import Image
from fastapi import UploadFile, HTTPException
import io
from typing import List, Dict, Any
from datetime import datetime, timezone
import logging
import time
import cv2
import numpy as np
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def processOCR (imageFile):
    """Reads an UploadFile, performs OCR, and returns the extracted text."""
    if not imageFile.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail = {
                "status": "fail",
                "message": "File berupa gambar (jpg, png, gif) diperlukan!",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    try:
        # Read image content into memory
        content = await imageFile.read()
        # Open image from memory
        img = Image.open(io.BytesIO(content))
        # Perform OCR
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logger.error(f"Error processing image {imageFile.filename}: {e}")
        # Consider raising a specific exception or returning an error indicator
        raise HTTPException(
            status_code=500, 
            detail={
                "status": "fail",
                "message": f"Failed to process image {imageFile.filename}: {str(e)}",
                }
            )
                
    
def parse_qty_return(val):
    val = val.lower().replace(',', '.')
    # Common OCR mistakes for numbers
    val = val.replace('l', '1').replace('o', '0').replace('L', '1').replace('|', '1')
    # Remove any non-numeric/non-dot characters that might remain
    val = re.sub(r'[^0-9.]', '', val)
    
    try:
        if val.startswith('0') and len(val) == 2:
            return float(f"0.{val[1]}")
        return float(val)
    except:
        return 0.0

async def getOrderNo (imageFile):
    """ OCR to get Order No"""
    try :
        startTime = time.time() # for debugging
        text =  await processOCR(imageFile)

        # Regex to get Order No
        # orderNoMatch = re.search(r'Order\s*No\s*[:\-]?\s*([A-Z0-9O]{2}/[0-9O]{2}-[0-9O]{4}/[0-9O]{3})', text, re.IGNORECASE)
        orderNoMatch = re.search(r'(OB/\d{2}-\d{4}/\d{3})', text)
        
        if orderNoMatch:
            extractedOrderNo = orderNoMatch.group(1)
        else:
            extractedOrderNo = "Not found"

        endTime = time.time() # for debugging
        processingTime = endTime - startTime # for debugging

        return {
            "status": "success",
            "message": "Order No extracted successfully",
            "data": {
                "filename": imageFile.filename,
                "orderNo": extractedOrderNo,
                "rawText": text, # Optionally return raw text for debugging
                "processingTime": processingTime # for debugging  
            }
        }
    

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan dalam proses OCR: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def getItemsData (imageFile):
    """ OCR to get Item Data"""
    try:
        startTime = time.time() # for debugging
        allText = ""
        itemResult = []
        
        for files in imageFile:
            if not files.filename:
                continue
            try:
                text = await processOCR(files)
                allText += text + "\n"
                
            except Exception as e:
                # Log error or collect filenames that failed
                logger.error(f"Skipping file {files.filename} due to processing error: {e}")
                # Optionally raise or return info about failed files
        
        lines = allText.splitlines()

        for line in lines:
            if not line.strip() or 'item' in line.lower():
                continue

            # Pattern 1: Ada return (Qty Return)
            match_return = re.match(r'^(\d+)\s+(.+?)\s+([0-9loiOIl,\.]+)\s+([0-9loiOIl,\.]+)\s+Rp', line)

            # Pattern 2: Tidak ada return (Qty langsung ke harga)
            match_no_return = re.match(r'^(\d+)\s+(.+?)\s+([0-9loiOIl,\.]+)\s+Rp', line)

            if match_return:
                no = int(match_return.group(1))
                item = match_return.group(2).strip()
                qty = parse_qty_return(match_return.group(3))
                ret = parse_qty_return(match_return.group(4))

                itemResult.append({
                    "No": no,
                    "Item": item,
                    "Qty": qty,
                    "Return": ret
                })
            elif match_no_return:
                no = int(match_no_return.group(1))
                item = match_no_return.group(2).strip()
                qty = parse_qty_return(match_no_return.group(3))

                itemResult.append({
                    "No": no,
                    "Item": item,
                    "Qty": qty,
                    "Return": 0.0
                })
        endTime = time.time() # for debugging
        processingTime = endTime - startTime # for debugging

        return {
            "status": "success",
            "message": "Item data extracted successfully",
            "data": {
                "itemsData": itemResult,
                "rawText": text, # Optionally return raw text for debugging
                "processingTime": processingTime # for debugging
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan dalam proses OCR: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def getReturnItems (imageFile):
    """ OCR to get Return Item Only"""
    try:
        startTime = time.time() # for debugging
        allText = ""
        itemResult = []
        
        for files in imageFile:
            if not files.filename:
                continue
            try:
                text = await processOCR(files)
                allText += text + "\n"
                
            except Exception as e:
                # Log error or collect filenames that failed
                logger.error(f"Skipping file {files.filename} due to processing error: {e}")
                # Optionally raise or return info about failed files
        
        lines = allText.splitlines()

        for line in lines:
            if not line.strip():
                continue
            
            # Pattern: No Item Qty Return Rp Harga Rp Total
            match = re.match(r'^(\d+)\s+(.+?)\s+([0-9loiOIl,\.]+)(?:\s+([0-9loiOIl,\.]+))?', line.strip())
            
            if match:
                no = int(match.group(1))
                item = match.group(2).strip()
                qty = parse_qty_return(match.group(3))
                ret = parse_qty_return(match.group(4)) if match.group(4) else 0.0
        
                if ret > 0:
                    itemResult.append({
                        "No": no,
                        "Item": item,
                        "Qty": qty,
                        "Return": ret
                    })


        endTime = time.time() # for debugging
        processingTime = endTime - startTime # for debugging

        return {
            "status": "success",
            "message": "Return Item berhasil diambil",
            "data": {
                "itemsData": itemResult,
                "rawText": text, # Optionally return raw text for debugging
                "processingTime": processingTime # for debugging
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan dalam proses OCR: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def scanBarcode(imageFile):
    """Scans an image for QR codes or barcodes and returns the decoded data"""
    try:
        startTime = time.time()  # for debugging
        
        # Check file type
        if not imageFile.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "File berupa gambar (jpg, png, gif) diperlukan!",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        # Read image content into memory
        content = await imageFile.read()
        
        # Convert to PIL Image
        pil_img = Image.open(io.BytesIO(content)).convert('RGB')
        
        # Convert PIL image to OpenCV format
        open_cv_image = np.array(pil_img)
        img = open_cv_image[:, :, ::-1].copy()  # RGB to BGR conversion for OpenCV
        
        # QR Code detection
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        
        if bbox is not None and data:
            # Found QR code with data
            if data.startswith('http://') or data.startswith('https://'):
                try:
                    # Fetch content from the URL
                    response = requests.get(data)
                    response.raise_for_status()
                    
                    # Parse HTML and extract text
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text(separator="\n")
                    
                    # Look for order number in the text
                    match = re.search(r'No\.\s*(OB/\d{2}-\d{4}/\d+)', text)
                    order_no = match.group(1) if match else "Not found"
                    
                    endTime = time.time()
                    processingTime = endTime - startTime
                    
                    return {
                        "status": "success",
                        "message": "QR code detected",
                        "data": {
                            "url": data,
                            "orderNo": order_no,
                            "processingTime": processingTime
                        }
                    }
                except Exception as e:
                    logger.error(f"Error processing URL from QR code: {e}")
                    
                    return {
                        "status": "partial_success",
                        "message": "QR code detected, but failed to fetch/extract data",
                        "data": {
                            "url": data,
                            "error": str(e)
                        }
                    }
            else:
                # QR code contains non-URL data
                endTime = time.time()
                processingTime = endTime - startTime
                
                return {
                    "status": "success",
                    "message": "QR code detected but data is not a URL",
                    "data": {
                        "content": data,
                        "processingTime": processingTime
                    }
                }
        else:
            # No QR code found
            endTime = time.time()
            processingTime = endTime - startTime
            
            return {
                "status": "fail",
                "message": "No QR code detected",
                "data": {
                    "processingTime": processingTime
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning barcode: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan dalam proses scan barcode: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
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
from app.config.firestore import db
from httpx import AsyncClient, HTTPStatusError

logger = logging.getLogger(__name__)

# Initialize PaddleOCR
# from paddleocr import PaddleOCR
# PaddleOCR = PaddleOCR( 
#         # use server version for better performance
#         # text_detection_model_name="PP-OCRv4_server_det",
#         # text_recognition_model_name="PP-OCRv4_server_rec",
#         ocr_version='PP-OCRv5', 
#         use_doc_orientation_classify=True,
#         use_doc_unwarping=True,
#         use_textline_orientation=True, 
#         lang='en',
#         device='cpu'
#     )

# PaddleOCR is deployed on a separate server
paddleOCR = None

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
                        "orderNo": "Null",
                        "processingTime": processingTime
                    }
                }
        else:
            # No QR code found, try OCR
            logger.info(f"No QR code detected in {imageFile.filename}. Attempting OCR.")
            # Reset file pointer for processOCR if it consumes the stream
            await imageFile.seek(0) 
            ocr_text = await processOCR(imageFile)
            
            endTime = time.time()
            processingTime = endTime - startTime
            
            # Attempt to find Order No in OCR text as a fallback
            orderNoMatch = re.search(r'(OB/\d{2}-\d{4}/\d{3})', ocr_text)
            extractedOrderNo = orderNoMatch.group(1) if orderNoMatch else "Not found in OCR"

            return {
                "status": "success",
                "message": "No QR code detected, OCR performed.",
                "data": {
                    "type": "ocr",
                    "rawText": ocr_text,
                    "orderNo": extractedOrderNo,
                    "processingTime": processingTime
                }
            }

            # # No QR code found
            # endTime = time.time()
            # processingTime = endTime - startTime
            
            # return {
            #     "status": "fail",
            #     "message": "No QR code detected",
            #     "data": {
            #         "processingTime": processingTime
            #     }
            # }
    
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
    
async def getOrderNoFromURL (url, currentUser): 
    """Extracts Order No from a given URL."""
    try : 
        # Check if user is admin or driver
        if currentUser["role"] not in ["admin", "driver"]:    
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk melakukan ini.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        startTime = time.time()  # for debugging
        if not url.startswith('http://') and not url.startswith('https://'):
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "URL tidak valid. Harus dimulai dengan http:// atau https://",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator="\n")
        
        # Look for order number in the text
        match = re.search(r'No\.\s*(OB/\d{2}-\d{4}/\d+)', text)
        order_no = match.group(1) if match else "Not found"
        
        endTime = time.time()
        processingTime = endTime - startTime
        
        if order_no == "Not found":
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": "Order No tidak ditemukan dalam URL yang diberikan.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        return {
            "status": "success",
            "message": "Order No extracted from URL",
            "data": {
                "url": url,
                "orderNo": order_no,
                "processingTime": processingTime
            }
        }
    
    except HTTPException:
        raise    
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Failed to process URL {url}: {str(e)}"
            }
        )

async def processPaddleOCR(imageFile):
    """Process image using PaddleOCR and return extracted text with coordinates."""
        # Check if PaddleOCR is properly initialized
    if paddleOCR is None:
        raise HTTPException(
            logger.error("PaddleOCR initialization failed. Check dependencies."),
            status_code=500,
            detail={
                "status": "fail",
                "message": "Saat ini fungsi OCR tidak tersedia. Silakan coba lagi nanti.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
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
        
        # Convert to numpy array for PaddleOCR
        image = Image.open(io.BytesIO(content))
        img_array = np.array(image)
        
        # Perform OCR with PaddleOCR
        result = paddleOCR.predict(img_array)
        return result
    except Exception as e:
        logger.error(f"Error processing image {imageFile.filename} with PaddleOCR: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "status": "fail",
                "message": f"Failed to process image {imageFile.filename}: {str(e)}",
                }
            )

def extract_table_data_from_paddle_result(paddle_result):
    """Extract table data from PaddleOCR 3.0.0 result by analyzing coordinates and text."""
    if not paddle_result or len(paddle_result) == 0:
        return []
    
    # PaddleOCR 3.0.0 returns a different structure
    # paddle_result is a list with one element containing the result dict
    result_dict = paddle_result[0]
    
    # Extract texts and coordinates
    rec_texts = result_dict.get('rec_texts', [])
    rec_polys = result_dict.get('rec_polys', [])
    rec_scores = result_dict.get('rec_scores', [])
    
    if not rec_texts or not rec_polys:
        return []
    
    # Extract all text boxes with their coordinates and text
    text_boxes = []
    for i, (text, poly, score) in enumerate(zip(rec_texts, rec_polys, rec_scores)):
        # Calculate center Y coordinate for row grouping from polygon
        y_coords = poly[:, 1]  # Extract Y coordinates
        x_coords = poly[:, 0]  # Extract X coordinates
        
        y_center = float(np.mean(y_coords))
        x_left = float(np.min(x_coords))
        
        text_boxes.append({
            'text': text.strip(),
            'y_center': y_center,
            'x_left': x_left,
            'confidence': float(score),
            'bbox': poly
        })
    
    # Sort by Y coordinate (top to bottom)
    text_boxes.sort(key=lambda x: x['y_center'])
    
    # Group text boxes into rows (same Y level) with improved threshold
    rows = []
    current_row = []
    y_threshold = 15  # Reduced threshold for better row detection
    
    for box in text_boxes:
        if not current_row:
            current_row.append(box)
        else:
            # Check if this box is on the same row as the previous ones
            avg_y = sum(b['y_center'] for b in current_row) / len(current_row)
            if abs(box['y_center'] - avg_y) <= y_threshold:
                current_row.append(box)
            else:
                # Sort current row by X coordinate (left to right)
                current_row.sort(key=lambda x: x['x_left'])
                rows.append(current_row)
                current_row = [box]
    
    # Don't forget the last row
    if current_row:
        current_row.sort(key=lambda x: x['x_left'])
        rows.append(current_row)
    
    return rows

def parse_delivery_order_rows(rows):
    """Parse rows with more flexible approach for incomplete tables."""
    items = []
    
    for row in rows:
        row_text = [box['text'] for box in row]
        full_row_text = ' '.join(row_text)
        
        # Skip completely empty rows or very short ones
        if not full_row_text.strip() or len(full_row_text.strip()) < 2:
            continue
            
        # Skip obvious header rows but be more specific
        if (full_row_text.strip().lower() in ['no', 'item', 'qty', 'return', 'no item qty return'] or
            'address' in full_row_text.lower() or
            'phone' in full_row_text.lower()):
            continue
        
        no_val = None
        item_name = ""
        qty_val = 0.0
        return_val = 0.0
        
        
        # Try to find patterns in the row
        for i, text in enumerate(row_text):
            text = text.strip()
            
            # Look for item number (single digit at start)
            if re.match(r'^\d+$', text) and len(text) <= 2:
                try:
                    potential_no = int(text)
                    if 1 <= potential_no <= 20:  # Reasonable item number range
                        no_val = potential_no
                        
                        # Collect subsequent text as item name until we hit numbers
                        item_parts = []
                        qty_candidates = []
                        
                        for j in range(i + 1, len(row_text)):
                            current_text = row_text[j].strip()
                            
                            # Skip empty
                            if not current_text:
                                continue
                            
                            # If it's a number, it might be quantity or return
                            if re.match(r'^\d+(\.\d+)?$', current_text):
                                try:
                                    val = float(current_text)
                                    if val <= 100:  # Reasonable quantity/return range
                                        qty_candidates.append(val)
                                except:
                                    pass
                            # If it contains letters and parentheses, likely part of item name
                            elif re.search(r'[a-zA-Z\(\)]', current_text):
                                item_parts.append(current_text)
                        
                        item_name = ' '.join(item_parts).strip()
                        
                        # Assign quantities
                        if len(qty_candidates) >= 2:
                            qty_val = qty_candidates[0]
                            return_val = qty_candidates[1]
                        elif len(qty_candidates) == 1:
                            qty_val = qty_candidates[0]
                            return_val = 0.0
                        
                        break
                except:
                    continue
        
        # Add item if we found valid data
        if no_val is not None and item_name and len(item_name) > 3:
            items.append({
                "No": no_val,
                "Item": item_name,
                "Qty": qty_val,
                "Return": return_val
            })
    
    return items

async def getReturnItemsPaddle(imageFile):
    """OCR to get Return Items using PaddleOCR."""
    try:
        startTime = time.time()
        files_to_send = []
        
        for files in imageFile:
            if not files.filename:
                continue
            
            # Check file type
            if not files.content_type.startswith('image/'):
                logger.warning(f"Skipping non-image file: {files.filename}")
                continue
            
            # Reset file pointer to beginning
            await files.seek(0)
            content = await files.read()
            
            # Prepare file tuple for multipart/form-data
            files_to_send.append(
                ('images', (files.filename, content, files.content_type))
            )
        
        if not files_to_send:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Tidak ada file gambar yang valid ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        async with AsyncClient() as client:
            response = await client.post(
                "https://pblpnj.lokatani.id/lokatrack/ocr/return",
                files=files_to_send,
                timeout=90
            )
            response.raise_for_status()
            
        response = response.json()

        return_items = response.get("data").get("returnItems", [])
        all_items = response.get("data").get("allItems", [])  # For debugging
        allText = response.get("data").get("allText", "")  # For debugging
        paddle_result = response.get("data").get("rawText", "")  # For debugging

        endTime = time.time()
        processingTime = endTime - startTime
        
        return {
            "status": "success",
            "message": "Return items extracted successfully using PaddleOCR",
            "data": {
                "returnItems": return_items,
                "allItems": all_items,  # For debugging
                "processingTime": processingTime, 
                "rawText": f"{paddle_result}",
                "allText": allText  # For debugging

            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in getReturnItemsPaddle: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan dalam proses OCR dengan PaddleOCR: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    

async def getReturnItemPaddleUsingDatabase (imagesFile, orderNo):
    """Get return item only using paddle OCR + match with database"""
    try :
        startTime = time.time()  # for debugging

        files_to_send = []
        for files in imagesFile:
            if not files.filename:
                continue
            
            # Check file type
            if not files.content_type.startswith('image/'):
                logger.warning(f"Skipping non-image file: {files.filename}")
                continue
            
            # Reset file pointer to beginning
            await files.seek(0)
            content = await files.read()
            
            # Prepare file tuple for multipart/form-data
            files_to_send.append(
                ('images', (files.filename, content, files.content_type))
            )
        
        if not files_to_send:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": "Tidak ada file gambar yang valid ditemukan",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        async with AsyncClient() as client:
            response = await client.post(
                "https://pblpnj.lokatani.id/lokatrack/ocr/return",
                files=files_to_send,
                timeout=90
            )
            response.raise_for_status()
            
        response = response.json()

        return_items = response.get("data").get("returnItems", [])
        all_items = response.get("data").get("allItems", [])  # For debugging
        allText = response.get("data").get("allText", "")  # For debugging
        paddle_result = response.get("data").get("rawText", "")  # For debugging



        # get items from database
        items_collection = (
            db.collection("packageOrderCollection")
            .document(orderNo.replace("/", "_"))  # Replace '/' with '-' for Firestore document ID
            .collection("items")
            .stream()
        )
        items_list = [item_doc.to_dict() for item_doc in items_collection]
        # item_list : [{'weight': 1.0, 'unitPrice': 20000.0, 'unitMetrics': 'Pack', 'type': 'CONVENT', 'total': 20000.0, 'quantity': 1.0, 'name': 'Tomat Cherry'}, {'weight': 250.0, 'unitPrice': 16500.0, 'unitMetrics': 'Gram', 'type': 'HYDROPONIC', 'total': 33000.0, 'quantity': 2.0, 'name': 'Romain'}, {'weight': 250.0, 'unitPrice': 18700.0, 'unitMetrics': 'Gram', 'type': 'HYDROPONIC', 'total': 37400.0, 'qal': 33000.0, 'quantity': 2.0, 'name': 'Romain'}, {'weight': 250.0, 'unitPrice': 18700.0, 'unitMetrics': 'Gram', 'type': 'HYDROPONIC', 'total': 37400.0, 'quantity': 2.0, 'name': 'oakleaf red'}, {'weight': 250.0, 'unitPrice': 20000.0, 'unitMetrics': 'Gram', 'type': 'CONVENT', 'total': 20000.0, 'quantity': 1.0, 'name': 'Endive'}]
        
    
        if not items_list:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"No items found for order {orderNo}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # Process OCR for all images
        all_ocr_items = all_items
        alltext = allText
        
        # Match OCR results with database items
        matched_items = []
        unmatched_ocr_items = []
        
        for ocr_item in all_ocr_items:
            matched = False
            ocr_item_name = ocr_item["Item"].lower().strip()
            
            # Try to find matching item in database
            for db_item in items_list:
                db_item_name = db_item["name"].lower().strip()
                
                # Simple string matching 
                if (ocr_item_name in db_item_name or 
                    db_item_name in ocr_item_name or
                    calculate_similarity(ocr_item_name, db_item_name) > 0.7):  # 70% similarity threshold
                    
                    # Create matched item with database info + OCR return quantity
                    matched_item = {
                        "No": ocr_item["No"],
                        "name": db_item["name"],
                        "weight": db_item.get("weight", 0),
                        "unitPrice": db_item.get("unitPrice", 0),
                        "unitMetrics": db_item.get("unitMetrics", ""),
                        "type": db_item.get("type", ""),
                        "total": db_item.get("total", 0),
                        "quantity": db_item.get("quantity", 0),
                        "ocrQuantity": ocr_item["Qty"],  # Quantity from OCR
                        "returnQuantity": ocr_item["Return"],  # Return quantity from OCR
                        "ocrItemName": ocr_item["Item"]  # Original OCR item name for reference
                    }
                    matched_items.append(matched_item)
                    matched = True
                    break
            
            if not matched:
                unmatched_ocr_items.append(ocr_item)
        
        # Filter only items with return > 0
        return_items = [item for item in matched_items if item["returnQuantity"] > 0]
        
        endTime = time.time()
        processingTime = endTime - startTime
        
        return {
            "status": "success",
            "message": "Berhasil melakukan OCR dan mencocokkan dengan database",
            "data": {
                "returnItems": return_items,
                "matchedItems": matched_items,  # All matched items
                "unmatchedOcrItems": unmatched_ocr_items,  # OCR items that couldn't be matched
                "databaseItems": items_list,  # Original database items for reference
                "processingTime": processingTime,
                "allText": alltext  # For debugging
            }
        }
    
    except HTTPException:
        raise    
    except Exception as e:
        logger.error(f"Error processing ocr: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Failed to process ocr: {str(e)}"
            }
        )

def calculate_similarity(str1, str2):
    """Calculate similarity between two strings using Levenshtein distance."""
    import difflib
    return difflib.SequenceMatcher(None, str1, str2).ratio()

def fuzzy_match_item_name(ocr_name, db_items, threshold=0.7):
    """Find the best matching item from database using fuzzy string matching."""
    best_match = None
    best_score = 0
    
    ocr_name_clean = ocr_name.lower().strip()
    
    for db_item in db_items:
        db_name_clean = db_item["name"].lower().strip()
        
        # Calculate similarity
        score = calculate_similarity(ocr_name_clean, db_name_clean)
        
        # Also check if one string contains the other
        if ocr_name_clean in db_name_clean or db_name_clean in ocr_name_clean:
            score = max(score, 0.8)  # Boost score for substring matches
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = db_item
    
    return best_match, best_score
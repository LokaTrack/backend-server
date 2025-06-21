from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import logging
from datetime import datetime, timezone
import time
from paddleocr import PaddleOCR
import uvicorn
import re

# This is an OCR microservice using PaddleOCR to detect text in images.
# PaddleOCR is resource-intensive, so it is better to run it on a separate server.
# Make sure PaddleOCR is properly installed:
# pip install paddlepaddle paddleocr
# pip install fastapi uvicorn Pillow numpy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OCR Microservice", 
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    root_path="/testing"
    )

# Initialize PaddleOCR once at startup
paddleOCR = None

@app.on_event("startup")
async def startup_event():
    global paddleOCR
    try:
        logger.info("Initializing PaddleOCR...")
        paddleOCR = PaddleOCR( 
            # use server version for better performance
            # text_detection_model_name="PP-OCRv4_server_det",
            # text_recognition_model_name="PP-OCRv4_server_rec",
            ocr_version='PP-OCRv5', 
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True, 
            lang='en',
            device='cpu'
        )
        logger.info("PaddleOCR initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR: {e}")
        raise

@app.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "paddleOCR_ready": paddleOCR is not None
    }

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
        return result, image
    except Exception as e:
        logger.error(f"Error processing image {imageFile.filename} with PaddleOCR: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "status": "fail",
                "message": f"Failed to process image {imageFile.filename}: {str(e)}",
                }
            )

def draw_ocr_results_on_image(image, paddle_result):
    """Draw OCR detection boxes and text on the image."""
    if not paddle_result or len(paddle_result) == 0:
        return image
    
    # Create a copy of the image to draw on
    img_with_boxes = image.copy()
    draw = ImageDraw.Draw(img_with_boxes)
    
    # Try to load a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    result_dict = paddle_result[0]
    rec_texts = result_dict.get('rec_texts', [])
    rec_polys = result_dict.get('rec_polys', [])
    rec_scores = result_dict.get('rec_scores', [])
    
    for i, (text, poly, score) in enumerate(zip(rec_texts, rec_polys, rec_scores)):
        # Convert polygon to list of tuples for drawing
        points = [(int(x), int(y)) for x, y in poly]
        
        # Draw bounding box
        draw.polygon(points, outline='red', width=2)
        
        # Draw text above the bounding box
        text_position = (int(poly[0][0]), int(poly[0][1]) - 25)
        draw.text(text_position, f"{text} ({score:.2f})", fill='blue', font=font)
    
    return img_with_boxes

@app.post("/ocr/visualize")
async def ocr_with_visualization(image: UploadFile = File(...)):
    """Perform OCR and return image with detected text boxes and recognized text."""
    
    if paddleOCR is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "fail",
                "message": "OCR service not ready. Please try again later.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    try:
        # Process with PaddleOCR
        paddle_result, original_image = await processPaddleOCR(image)
        
        # Draw OCR results on image
        image_with_boxes = draw_ocr_results_on_image(original_image, paddle_result)
        
        # Convert image to bytes for streaming response
        img_buffer = io.BytesIO()
        image_with_boxes.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(img_buffer.read()),
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=ocr_result.png"}
        )
        
    except Exception as e:
        logger.error(f"Error in ocr_with_visualization: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"OCR visualization failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

@app.post("/ocr/table")
async def ocr_table_detection(image: UploadFile = File(...)):
    """Perform OCR and return text organized by rows for table recognition."""
    time_start = time.time()
    
    if paddleOCR is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "fail",
                "message": "OCR service not ready. Please try again later.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    try:
        # Process with PaddleOCR
        paddle_result, _ = await processPaddleOCR(image)
        
        # Extract table structure using existing function
        rows = extract_table_data_from_paddle_result(paddle_result)
        
        # Format rows for simple response - just text per row
        table_rows = []
        for i, row in enumerate(rows):
            row_texts = [box["text"] for box in row]
            full_row_text = " ".join(row_texts)
            table_rows.append(f"Baris {i + 1}: {full_row_text}")
        
        end_time = time.time()
        processing_time = end_time - time_start
        
        return {
            "status": "success",
            "message": "Table OCR completed successfully",
            "data": {
                "processingTime": processing_time,
                "totalRows": len(table_rows),
                "tableRows": table_rows
            }
        }
        
    except Exception as e:
        logger.error(f"Error in ocr_table_detection: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Table OCR failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
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

@app.post("/ocr/return")
async def process_return_items(images: List[UploadFile] = File(...)):
    """Process images for return items using PaddleOCR - equivalent to getReturnItemsPaddle logic."""
    timeStart = time.time()
    if paddleOCR is None:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "fail",
                "message": "OCR service not ready. Please try again later.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    try:
        all_items = []
        alltext = ""
        
        for files in images:
            if not files.filename:
                continue
            try:
                # Process with PaddleOCR
                paddle_result, _ = await processPaddleOCR(files)
                
                # Extract table structure
                rows = extract_table_data_from_paddle_result(paddle_result)

                # Parse delivery order data
                items = parse_delivery_order_rows(rows)

                all_items.extend(items)
                
                # Get all text from paddle_result for debugging
                if paddle_result and len(paddle_result) > 0:
                    result_dict = paddle_result[0]
                    rec_texts = result_dict.get('rec_texts', [])
                    for text in rec_texts:
                        alltext += text + "\n"
                        
            except Exception as e:
                logger.error(f"Skipping file {files.filename} due to processing error: {e}")
                continue
        
        # Filter only items with return > 0
        return_items = [item for item in all_items if item["Return"] > 0]
        endTime = time.time()
        processingTime = endTime - timeStart
        return {
            "status": "success",
            "message": "Return items processed successfully",
            "data": {
                "processingTime": processingTime,
                "returnItems": return_items,
                "allItems": all_items,
                "allText": alltext,  # For debugging
                "rawText": f"{paddle_result}"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in process_return_items: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"OCR processing failed: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9898)
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import logging
from typing import Dict, Union, Any, Optional
from datetime import datetime, timezone
import uuid
import pyvips
import os
from io import BytesIO
import time

logger = logging.getLogger(__name__)

async def compress_image (
    image_file, 
    quality: int = 75, 
    resize_width: Optional[int] = None,
    compression_level: Optional[int] = None,
    resize_height: Optional[int] = None,
    max_size_kb: Optional[int] = None,
    is_lossless: bool = False,
    return_buffer: bool = True, # DEFAULT Return as buffer
    return_image: bool = False
):
    try : 
        # read file image and save to buffer
        fileBytes = await image_file.read()
        await image_file.seek(0)  # Reset the file pointer to the beginning

        # Load image from memory
        image = pyvips.Image.new_from_buffer(fileBytes, "")

        # ORIGINAL Statistics
        content_type = image_file.content_type
        extension = os.path.splitext(image_file.filename)[1][1:].lower()
        original_filename = image_file.filename    
        original_size = len (fileBytes) # in bytes
        original_width = image.width
        original_height = image.height
              
        # Process with VIPS
        start_time = time.time()

        # Default resize for very large images
        if not resize_width and not resize_height and (original_width > 1600 or original_height > 1600):
            resize_width = 1600  # Reasonable default size for web
            scale = resize_width / image.width
            image = image.resize(scale)

        # Resize if dimensions are provided
        if resize_width and resize_height:
            image = image.thumbnail_image(resize_width, height=resize_height, size="down")
        elif resize_width:
            scale = resize_width / image.width
            image = image.resize(scale)
        elif resize_height:
            scale = resize_height / image.height
            image = image.resize(scale)
        
        if is_lossless:
            output_format = ".png"
            output_mime = "image/png"
            compression_level = min(9, int(9 * (100 - quality) / 100))
            compression_level = 1 if compression_level < 1 else compression_level
            compressed_image = image.write_to_buffer(".png", compression = compression_level) # save image to png lossless format 
        # <--- parameter  --->
        # JPG, JPEG, WEBP, and others
        #  - Quality (1-100),       Higher compression level means LOWER quality
        #  - strip=True	            Hapus metadata (EXIF, ICC)
        #
        #  - optimize_coding=True	Gunakan Huffman table optimal (ukuran file lebih kecil) -> only for jpg
        #
        #  PNG
        #  - filter	                Filter PNG predictor (0–5, default: libvips pilih otomatis)
        #  - compression (0-9)	    Higher compression level means LOWER quality (default 6), 9 = kompresi maksimal  
        #                           Higher quality → Lower compression level 
        #                           Lower quality → Higher compression level
        # <--- parameter  --->
        else :
            # for lossy format
            if extension in ["jpg", "jpeg"]:
                utput_format = ".jpg"
                output_mime = "image/jpeg"
                compressed_image = image.write_to_buffer(".jpg", Q=quality, strip=True)
            elif extension == "png":
                compression_level = min(9, int(9 * (100 - quality) / 100))# -> to convert quality to compression level
                compression_level = 1 if compression_level < 1 else compression_level # if quality > 85 compression level will 0 (error)
                output_format = ".png"
                output_mime = "image/png"
                compressed_image = image.write_to_buffer(".png", compression=compression_level)
            elif extension == "webp":
                output_format = ".webp"
                output_mime = "image/webp"
                compressed_image = image.write_to_buffer(".webp", lossless=True, strip=True)
            else: # Default to JPEG for unsupported formats
                output_format = ".jpg"
                output_mime = "image/jpeg"
                compressed_image = image.write_to_buffer(".jpg", Q=quality, strip=True)
        
        # Check if size needs to be further reduced (adaptive quality)
        if max_size_kb and not is_lossless:
            print ("i will compress because max_size_kb is not None")
            current_quality = quality
            max_bytes = max_size_kb * 1024
            current_size = len(compressed_image)
            
            # Try with progressively lower quality if still too large
            while current_size > max_bytes and current_quality > 20:
                print ("compress again ... ")
                current_quality -= 5 
                if output_format == ".webp":
                    compressed_image = image.write_to_buffer(".webp", Q=current_quality, strip=True)
                else:
                    compressed_image = image.write_to_buffer(".jpg", Q=current_quality, optimize_coding=True, strip=True)
                current_size = len(compressed_image)

        processing_time = time.time() - start_time
        compressed_size = len(compressed_image) 
        compressed_ratio = (original_size / compressed_size) if compressed_size > 0 else float('inf')
        space_saved_percent = ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
        
        if return_buffer:
            return compressed_image

        if return_image : 
            return StreamingResponse (
                content=BytesIO(compressed_image), 
                media_type=output_mime,
                headers={
                    "Content-Disposition": f"inline; filename={os.path.splitext(original_filename)[0]}_compressed.jpg"
                }
            )
        else : 
            original_statistics = {
                "original_size_bytes": original_size,
                "original_size_kb": f"{original_size/1024:.2f} KB",
                "original_dimensions": f"{original_width}x{original_height}",
                "content_type": content_type,
            }
            compressed_statistics = {
                "compressed_size_bytes": compressed_size,
                "compressed_size_kb": f"{compressed_size/1024:.2f} KB",
                "compressed_dimensions": f"{image.width}x{image.height}",
                "compressed_content_type": output_mime,                
            }
            image_data = {
                "original_filename": original_filename,
                # if png compression level, if jpg quality
                f"{'compression_level' if compression_level else 'quality'}" : f"{compression_level if compression_level else current_quality}",
                "compression_ratio": f"{compressed_ratio:.2f}x",
                "space_saved_percent": f"{space_saved_percent:.2f}% ({(original_size-compressed_size)/1024:.2f} KB)",
                "space_saved_kb": f"{round((original_size - compressed_size) / 1024, 2):.2f} KB",                
                "processing_time": f"{processing_time:.3f} seconds",
            }
            return {
                "status": "success",
                "message": "Image compressed successfully",
                "data": {
                    "original": original_statistics,
                    "compressed": compressed_statistics,
                    "image_data": image_data
                }
            }


    except Exception as e:
        logger.error(f"Error while compressing image  : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Server Error while compressing image: {str(e)}"
        )
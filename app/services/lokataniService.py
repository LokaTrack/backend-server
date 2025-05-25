import httpx
import urllib
import asyncio
from app.models.packageModel import packageOrderModel, orderItemModel
from fastapi import HTTPException
from app.services.packageService import addPackage
from httpx import AsyncClient, HTTPStatusError
import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import Optional

logger = logging.getLogger(__name__)
load_dotenv()

LOKATANI_API_KEY = os.getenv("LOKATANI_API_KEY")
LOKATANI_API_URL = os.getenv("LOKATANI_API_URL")

# Data Sementara
LOKATANI_USERNAME = os.getenv("LOKATANI_USERNAME")
LOKATANI_PASSWORD = os.getenv("LOKATANI_PASSWORD")

async def authLokatani(username: str, password: str) :
    """Authenticate/Login to Lokatani API and return the dict for access token.
    
    Args:
        username: User's username or email
        password: User's password
    
    Returns:
        ```
        {
            "code": 200,
            "status": "Success",
            "message": "Success login",
            "data": {
                "token": "xxxxxxxxxx",
                "email": "xxxx",
                "name": "Amrixxxxx"
            }
        }
        ```
    
    Raises:
        HTTPException: If authentication fails or there's a connection issue
    """
    try :
        async with AsyncClient() as client: 
            formData = {
                # "username": username,
                # "password": password
                # Credential sementara
                "username" : LOKATANI_USERNAME,
                "password" : LOKATANI_PASSWORD
            }

            headers = {
                "api-key": LOKATANI_API_KEY,
            }

            # Send post async request to Lokatani API
            response = await client.post(
                f"{LOKATANI_API_URL}/user/login",
                data=formData,
                headers=headers,
                timeout=10.0
            )

            # Check external API response
            response.raise_for_status()
            return response.json()

    except HTTPStatusError as http_err:
        logger.error(f"External API authentication failed: {str(http_err)}")
        statusCode = http_err.response.status_code
        errorData = http_err.response.json()
        errorMessage = errorData.get("info", "Unknown error from external API")
        
        raise HTTPException(
            status_code=statusCode,
            detail={
                "status": "fail",
                "message": errorMessage,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as ext_err:
        logger.error(f"Error connecting to external API: {str(ext_err)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": "Failed to connect to LokaTani API",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def getPackageFromLokaTani(orderNo, sessionToken):
    """Get Package Detail from LokaTani API by Order Number."""
    try : 
        # async with AsyncClient() as client:
        #     # Prepare form data and headers for authentication

        async with AsyncClient() as client:   
            formData = {
                "delivery_order_number" : orderNo
            }
    
            headers = {
                "api-key": LOKATANI_API_KEY,
                "sess-token": sessionToken
            }
    
            # Send post async request to Lokatani API
            response = await client.post(
                f"{LOKATANI_API_URL}/order/get",
                data=formData,
                headers=headers,
                timeout=10.0
            )
            
            # Check external API response
            response.raise_for_status()
            return response.json()
            

    except HTTPStatusError as http_err:
        logger.error(f"External API authentication failed: {str(http_err)}")
        
        statusCode = http_err.response.status_code
        errorData = http_err.response.json()
        errorMessage = errorData.get("info", "Unknown error from external API")

        raise HTTPException(
            status_code=statusCode, 
            detail={
                "status": "fail",
                "message": errorMessage,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    except Exception as ext_err:
        logger.error(f"Error connecting to external API: {str(ext_err)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Failed to connect to LokaTani API",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def convertLokataniToPackageModel(lokataniData):
    """
    Convert Lokatani API response to packageOrderModel format
    
    Args:
        lokataniData (dict): Response from Lokatani API
        
    Returns:
        packageOrderModel: Converted package model
    """
    try:
        # Extract order data
        order_data = lokataniData.get("data", {})
        
        # <-- Extract Id Order -->
        order_id = order_data.get("order_id") #https://orders.lokatani.id/order/view/order_id
        order_number = order_data.get("order_number")
        invoice_number = order_data.get("invoice_number", "")
        # <-- Extract customer info -->


        # <-- Extract customer info -->
        customer_data = order_data.get("customer", {})
        customer_name = customer_data.get("name", "")
        phone = customer_data.get("phone", "")
        address = customer_data.get("address", "")
        customer_type = customer_data.get("type")
        
        # Create address map URL
        address_map_url = None
        if address:
            encoded_address = urllib.parse.quote(address)
            address_map_url = f"https://www.google.com/maps/search/?api=1&query={encoded_address}"
        # <-- Extract customer info -->


        # Convert date from "YYYY-MM-DD" to datetime object
        order_date_str = order_data.get("order_at", "")
        invoice_due_at = order_data.get("invoice_due_at", "")
        try:
            order_date = datetime.strptime(order_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            invoice_due_at = datetime.strptime(invoice_due_at, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            order_date = datetime.now(timezone.utc)
            invoice_due_at = None
        
        # <-- Extract payment details -->
        payment_details = order_data.get("payment_amount_detail", {})
        
        # Handle price values - Lokatani uses raw values,
        sub_total = float(payment_details.get("subtotal", 0))
        shipping = float(payment_details.get("shipping", 0))
        total_price = float(order_data.get("payment_amount_total", 0))
        
        # Calculate discount (since it's not explicitly provided)
        # If total doesn't match subtotal + shipping, assume the difference is discount
        expected_total = sub_total + shipping
        discount = max(0, expected_total - total_price) if expected_total > total_price else 0
        
        payment_status = payment_details.get("payment_status")
        # <-- Extract payment details -->


        # Process items
        items_data = order_data.get("items", [])
        items = []
        total_weight = 0.0
        
        for item in items_data:
            # Extract item data with safety checks
            weight_per_unit = float(item.get("weight", 0))
            quantity = float(item.get("quantity", 0))
            unit_price = float(item.get("unit_price", 0))
            total = float(item.get("total_price", 0))
            type = item.get("type")  # Default to HYDROPONIC if type is not provided
            unit_metrics = item.get("unit_metrics", "Kg")
            
            # Create item model
            item_model = orderItemModel(
                name=item.get("name"),
                quantity=quantity,
                unitPrice=unit_price,
                total=total,
                weight=weight_per_unit,
                type=type,
                unitMetrics=unit_metrics
            )
            
            items.append(item_model)
            
            # Calculate total weight (weight per unit × quantity)
            total_weight += weight_per_unit * quantity
        
        # Create the package order model
        order_notes = order_data.get("order_note", "")
        
        package_model = packageOrderModel(
            orderNo=order_number,
            orderId=order_id,  
            invoiceNo=invoice_number, 
            orderDate=order_date,
            invoiceDueAt=invoice_due_at,
            customer=customer_name,
            address=address,
            costomerType = customer_type,
            addressMapUrl=address_map_url,
            phone=phone,
            items=items,
            orderNotes=order_notes,
            totalWeight=total_weight,
            subTotal=sub_total,
            discount=discount,
            shipping=shipping,
            totalPrice=total_price,
            paymentStatus=payment_status,
        )
        
        return package_model
        
    except Exception as e:
        logger.error(f"Error converting Lokatani data to package model: {str(e)}")
        raise ValueError(f"Failed to convert Lokatani data: {str(e)}")
    
async def addLokataniPackage(orderNo, current_user):
    """
    Get package data from Lokatani API and add it to the database
    
    Args:
        order_no: Order number to fetch from Lokatani API
        session_token: Lokatani API session token
        current_user: Current authenticated user
        
    Returns:
        dict: Response with package data
    """
    
    try:
        # Get package data from Lokatani API
        lokataniResponse = await getPackageFromLokaTani(orderNo, current_user.get("lokataniSession"))

        # Convert to packageOrderModel
        packageModel = await convertLokataniToPackageModel(lokataniResponse)
        
        # Add package to lokatrack database using existing addPackage function
        result = await addPackage(packageModel, current_user)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding Lokatani package: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Failed to process Lokatani order: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
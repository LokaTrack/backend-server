from urllib.parse import unquote
from app.config.firestore import db
from fastapi import HTTPException
from datetime import datetime, timezone
from app.utils.location import getPackageLocation
from uuid import uuid4
from app.utils.time import convert_utc_to_wib
import logging
logger = logging.getLogger(__name__)

# ADD Package to packageDeliveryCollection and Change status to delivery
async def startDeliveryPackage(deliveryDataInput, currentUser):
    try:
        # Check if user is admin or driver
        if currentUser["role"] not in ["admin", "driver"]:    
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk menambahkan order.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # filter / to _
        deliveryData = deliveryDataInput.dict()
        orderNoFiltered = deliveryData["orderNo"].replace("/", "_")

        # Check if package exists in packageOrderCollection
        packageOrderDoc = (
            db.collection("packageOrderCollection")
            .document(orderNoFiltered)
            .get()
        )
        # <google.cloud.firestore_v1.base_document.DocumentSnapshot object at 0x000001FC09D54210>
        if not packageOrderDoc.exists: 
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{deliveryDataInput.orderNo}' tidak ditemukan.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        packageOrderDoc = packageOrderDoc.to_dict()
        
        # check if package status is already "dikirim"
        packageDeliveryDoc = ( 
            db.collection("packageDeliveryCollection")
            .document(orderNoFiltered)
            .get()
        )
        if packageDeliveryDoc.exists :
            status = packageDeliveryDoc.to_dict().get("deliveryStatus")
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{deliveryDataInput.orderNo}' sudah dalam status '{status}'.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # get package location
        # packageLocation = await getPackageLocation(deliveryDataInput.trackerId)
        # deliveryDataInput.deliveryStartLocation = packageLocation

        # Update data
        newPackageData= deliveryDataInput.dict()
        newPackageData.update({
            "driverId": currentUser["userId"],
            "customer": packageOrderDoc["customer"],
            "address": packageOrderDoc["address"],
            "itemsList": packageOrderDoc["itemsList"],
            "totalWeight": packageOrderDoc["totalWeight"],
            "totalPrice": packageOrderDoc["totalPrice"],
            "orderNotes": packageOrderDoc["orderNotes"],
        })

        db.collection("packageDeliveryCollection").document(orderNoFiltered).set(newPackageData)
        
        # update to wib in response 
        newPackageData.update({
            "deliveryStartTime": convert_utc_to_wib(newPackageData["deliveryStartTime"]),
            "lastUpdateTime": convert_utc_to_wib(newPackageData["lastUpdateTime"]),
        })
        return {
            "status": "success",
            "message": "Paket berhasil ditambahkan ke delivery",
            "data": newPackageData
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during package status update for '{deliveryDataInput.orderNo}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
async def updateDeliveryStatus (deliveryDataInput, currentUser):
    try:
        # Check if user is admin or driver
        if currentUser["role"] not in ["admin", "driver"]:    
            logger.warning(f"User '{currentUser['username']}' tidak memiliki akses untuk mengubah status.")
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk mengupdate order.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )       
        
        # filter / to _
        deliveryData = deliveryDataInput.dict()
        orderNoFiltered = deliveryData["orderNo"].replace("/", "_")

        # Validate if the package exists in Firestore's packageDeliveryCollection
        packageDeliveryDoc = (
            db.collection("packageDeliveryCollection")
            .document(orderNoFiltered)
            .get()
        )
        if not packageDeliveryDoc.exists: 
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{deliveryDataInput.orderNo}' tidak ditemukan.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        packageDeliveryData = packageDeliveryDoc.to_dict()

        # Check if the user has permission to modify the package
        if packageDeliveryData.get("driverId") != currentUser["userId"] and currentUser["role"] != "admin":
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": f"Anda tidak memiliki akses untuk mengupdate paket dengan id '{deliveryDataInput.orderNo}'.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        # status -> "On Delivery", "Check-in", "Check-out", "Return"
        valid_status_transitions = {
            "On Delivery": "Check-in",
            "Check-in": "Check-out",
            "Check-out": "Return",
            "Return": "Check-out"
        }

        current_status = packageDeliveryData.get("deliveryStatus")
        next_status = deliveryDataInput.deliveryStatus.value

        if valid_status_transitions.get(current_status) != next_status:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": f"Tidak bisa mengubah status paket dari '{current_status}' menjadi '{next_status}'.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        time_field_mapping = {
            "Check-in": "checkInTime",
            "Check-out": "checkOutTime",
            "Return": "returnTime"
        }
        time_field_to_update = time_field_mapping.get(next_status)

        update_data = {
            "deliveryStatus": next_status,
            "lastUpdateTime": datetime.now(timezone.utc)
        }

        if time_field_to_update:
            update_data[time_field_to_update] = datetime.now(timezone.utc)
        
        packageDeliveryData.update(update_data)        
        # packageDeliveryData.update({
        #     "deliveryStatus": deliveryDataInput.deliveryStatus,
        #     "checkInTime": deliveryDataInput.checkInTime,
        #     "lastUpdateTime": deliveryDataInput.lastUpdateTime,
        # })
                
               
        db.collection("packageDeliveryCollection").document(orderNoFiltered).update(packageDeliveryData)

        # update response to wib
        time_fields = ["deliveryStartTime", "checkInTime", "checkOutTime", "returnTime", "lastUpdateTime"]
        for field in time_fields:
            if field in packageDeliveryData and packageDeliveryData[field]:
                packageDeliveryData[field] = convert_utc_to_wib(packageDeliveryData[field])
        
        return {
            "status": "success",
            "message": f"Status paket '{deliveryDataInput.orderNo}' berhasil diupdate",
            "data": packageDeliveryData
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during package status update for '{deliveryDataInput.orderNo}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def getPackageDeliveryById(orderNo):
    try:
        orderNo = unquote(orderNo)
        orderNoFiltered = orderNo.replace("/", "_")
        # Get package delivery data by ID
        packageDeliveryDoc = (
            db.collection("packageDeliveryCollection")
            .document(orderNoFiltered)
            .get()
        )
        if not packageDeliveryDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{orderNo}' tidak ditemukan.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        packageDeliveryData = packageDeliveryDoc.to_dict()
        
        # Convert time fields in response to WIB
        time_fields = ["deliveryStartTime", "checkInTime", "checkOutTime", "returnTime", "lastUpdateTime"]
        for field in time_fields:
            if field in packageDeliveryData and packageDeliveryData[field]:
                packageDeliveryData[field] = convert_utc_to_wib(packageDeliveryData[field])
          
        # update response items list to string
        list_item = ', '.join(packageDeliveryData["itemsList"])
        packageDeliveryData["itemsList"] = list_item
        
        return {
            "status": "success",
            "message": "Mengambil data pengiriman berhasil",
            "data": packageDeliveryData
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during get delivery detail for '{orderNo}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def getAllPackageDelivery():
    try:
        # Get all package delivery data
        packageDeliveryDocs = (
            db.collection("packageDeliveryCollection")
            .stream()
        )
        if not packageDeliveryDocs:
            return {
                "status": "success",
                "message": "Tidak ada data pengiriman",
                "data": []
            }
        
        packageDeliveryList = [packageDeliveryDoc.to_dict() for packageDeliveryDoc in packageDeliveryDocs]
        
        return {
            "status": "success",
            "message": "Mengambil data pengiriman berhasil",
            "data": packageDeliveryList
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during get all pacakge :' {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
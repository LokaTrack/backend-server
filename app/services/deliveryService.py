
import urllib
from urllib.parse import unquote
from app.config.firestore import db
from fastapi import HTTPException
from datetime import datetime
from app.models.packageModel import  packageOrderModel, orderItemModel
from app.models.deliveryModel import packageDeliveryModel
from app.utils.location import getPackageLocation
from uuid import uuid4
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
                    "timestamp": datetime.now().isoformat()
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
        if not packageOrderDoc.exists: 
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{deliveryDataInput.orderNo}' tidak ditemukan.",
                    "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
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
            "totalWeight": packageOrderDoc["totalWeight"],
            "totalPrice": packageOrderDoc["totalPrice"]
        })

        db.collection("packageDeliveryCollection").document(orderNoFiltered).set(newPackageData)

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
                "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
                }
            )
        # status -> "delivery", "checkin", "checkout", "return"
        valid_status_transitions = {
            "delivery": "checkin",
            "checkin": "checkout",
            "checkout": "return",
            "return": "checkout"
        }

        current_status = packageDeliveryData.get("deliveryStatus")
        next_status = deliveryDataInput.deliveryStatus.value

        if valid_status_transitions.get(current_status) != next_status:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": f"Tidak bisa mengubah status paket dari '{current_status}' menjadi '{next_status}'.",
                    "timestamp": datetime.now().isoformat()
                }
            )

        time_field_mapping = {
            "checkin": "checkInTime",
            "checkout": "checkOutTime",
            "return": "returnTime"
        }
        time_field_to_update = time_field_mapping.get(next_status)

        update_data = {
            "deliveryStatus": next_status,
            "lastUpdateTime": datetime.now().isoformat()
        }

        if time_field_to_update:
            update_data[time_field_to_update] = datetime.now().isoformat()
        
        packageDeliveryData.update(update_data)        
        # packageDeliveryData.update({
        #     "deliveryStatus": deliveryDataInput.deliveryStatus,
        #     "checkInTime": deliveryDataInput.checkInTime,
        #     "lastUpdateTime": deliveryDataInput.lastUpdateTime,
        # })
                
               
        db.collection("packageDeliveryCollection").document(orderNoFiltered).update(packageDeliveryData)

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
                "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        packageDeliveryData = packageDeliveryDoc.to_dict()
        
        return {
            "status": "success",
            "message": "Mengambil data pengiriman berhasil",
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
                "timestamp": datetime.now().isoformat()
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
        logger.error(f"Unexpected error during package status update for '{deliveryDataInput.orderNo}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
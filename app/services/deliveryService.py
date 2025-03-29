
import urllib
from app.config.firestore import db
from fastapi import HTTPException
from datetime import datetime
from app.models.packageModel import  packageOrderModel, orderItemModel
from app.models.deliveryModel import packageDeliveryModel
from app.utils.location import getPackageLocation
from uuid import uuid4

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
        print(f"Error tidak terduga: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )
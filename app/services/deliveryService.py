from app.models.deliveryModel import packageDeliveryReturnModel, returnItemsModel
from app.utils.storeImage import uploadBytesToStorage
from app.utils.compress import compress_image
from app.utils.time import convert_utc_to_wib
from app.config.firestore import db
from app.services.lokataniService import addLokataniPackage
from datetime import datetime, timezone
from google.cloud.firestore import DELETE_FIELD
from fastapi import HTTPException
from urllib.parse import unquote
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
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        
        # filter / to _
        deliveryData = deliveryDataInput.dict()
        orderNoFiltered = deliveryData["orderNo"].replace("/", "_")

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

        await addLokataniPackage(deliveryData.get("orderNo"), currentUser)

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

async def updateDeliveryStatusReturn(listImages, orderNo, returnItems, reason, currentUser):
    try:
        # Check if user is admin or driver
        if currentUser["role"] not in ["admin", "driver"]:    
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk mengupdate order.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )       

        # Validate if the package exists in Firestore's packageDeliveryCollection
        orderNoFiltered = orderNo.replace("/", "_")
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

        # Check if the user has permission to modify the package
        if packageDeliveryData.get("driverId") != currentUser["userId"] and currentUser["role"] != "admin":
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": f"Anda tidak memiliki akses untuk mengupdate paket dengan id '{orderNo}'.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        # status -> "On Delivery", "Check-in", "Check-out", "Return"
        valid_status_transitions = {
            "On Delivery": "invalid",
            "Check-in": "Return", 
            "Check-out": "invalid", 
            "Return": "invalid"
        }

        currentStatus = packageDeliveryData.get("deliveryStatus")
        nextStatus = "Return" # next status is must return

        if valid_status_transitions.get(currentStatus) != nextStatus:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "fail",
                    "message": f"Tidak bisa mengubah status paket dari '{currentStatus}' menjadi '{nextStatus}'.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        # loopng check return items in deliveryData
        itemsOrderCollection = (
            db.collection("packageOrderCollection")
            .document(orderNoFiltered)
            .collection("items")
            .get()
        )
        orderItems = [item.to_dict() for item in itemsOrderCollection]

        # check if items in return data is in orderItems
        for item in returnItems:
            itemMatch = False
            for orderItem in orderItems:
                if item["name"] == orderItem["name"]:     
                    itemMatch = True
                    # check if item quantity is more than order quantity
                    if item["quantity"] > orderItem["quantity"]:
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "status": "fail",
                                "message": f"Jumlah item '{item['name']}' yang ingin dikembalikan melebihi jumlah yang dipesan.",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        )
                    break
            if not itemMatch:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "fail",
                        "message": f"Item dengan id '{item['itemId']}' tidak ditemukan dalam order.",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            
        # complete data in returnItems
        for item in returnItems:
            for orderItem in orderItems:
                if item["name"] == orderItem["name"]:
                    item["weight"] = orderItem["weight"]
                    item["unitMetrics"] = orderItem["unitMetrics"]
                    item["unitPrice"] = orderItem["unitPrice"]
                    item["total"] = item["quantity"] * item["unitPrice"]
                    break
        

        returnItemsList = []
        for item in returnItems:
            returnItem = returnItemsModel(
                unitName=item["name"],
                weight=item["weight"],
                quantity=item["quantity"],
                unitMetrics=item["unitMetrics"],
                unitPrice= item["unitPrice"],
                total=item["total"],
            ) 
            returnItemsList.append(returnItem.dict())

        totalWeight = sum(item["weight"] * item["quantity"] for item in returnItems)
        totalPrice = sum(item["total"] for item in returnItems)
        totalItems = len(returnItems)

        deliveryOrderURL = []
        for image in listImages : 
            counter = 1
            image_file = await image.read()
            imageSize = len(image_file) / 1024  # Convert to KB
            maxSize = 1024 * 1024 * 10 # 10 MB

            if imageSize > maxSize:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "fail",
                        "message": "Ukuran file terlalu besar, maksimal 10MB",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                )
            await image.seek(0)

            filename = f"return_{orderNoFiltered}_{counter}"
            fileExtension = image.filename.split(".")[-1]
            fullFilename = f"{filename}.{fileExtension}"

            # compressed image
            compressed_image, output_mime = await compress_image(image_file=image, max_size_kb=1024)  # type: ignore

            imageUrl = await uploadBytesToStorage(
                bytes=compressed_image,
                location="return-delivery-order", # folder in storage bucket
                fileName=fullFilename,
                content_type=output_mime
            )
            deliveryOrderURL.append(imageUrl)
            counter += 1

        # Update data
        returnPackageData = packageDeliveryReturnModel(
            orderNo=orderNo,
            returnId=str(uuid4()),
            deliveryOrderImages=deliveryOrderURL,
            returnDate=datetime.now(timezone.utc),
            returnedItems=returnItemsList,
            totalWeight=totalWeight,
            totalPrice=totalPrice,
            totalItems=totalItems,
            reason=reason,
        ).dict()

        batch = db.batch()
        
        # Update packageReturnCollection
        packageReturnCollectionRef = db.collection("packageReturnCollection").document(orderNoFiltered)
        batch.set(packageReturnCollectionRef, returnPackageData)

        # Update packageDeliveryCollection, update delivery status to return
        packageDeliveryCollectionRef = db.collection("packageDeliveryCollection").document(orderNoFiltered)
        packageDeliveryData = {
            "checkOutTime": DELETE_FIELD,
            "deliveryStatus": "Return",
            "returnTime": datetime.now(timezone.utc),
            "lastUpdateTime": datetime.now(timezone.utc)
        }
        batch.update(packageDeliveryCollectionRef, packageDeliveryData)

        # Commit all changes
        batch.commit()
        return {
            "status": "success",
            "message": f"Status paket '{orderNo}' berhasil diupdate menjadi 'Return'",
            "data": returnPackageData
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during update '{orderNo}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def getPackageReturnById(orderNo, currentUser):
    try:
        # Check if user is admin or driver
        if currentUser["role"] not in ["admin", "driver"]:    
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk mengupdate order.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )   
        orderNo = unquote(orderNo)
        orderNoFiltered = orderNo.replace("/", "_")
        # Validate if the package exists in Firestore's packageDeliveryCollection
        deliveryReturnDoc = (
            db.collection("packageReturnCollection")
            .document(orderNoFiltered)
            .get()
        )
        if not deliveryReturnDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{orderNo}' tidak ditemukan.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        deliveryReturnData = deliveryReturnDoc.to_dict()

        # Convert floats to ints if they are whole numbers
        for field in ['totalWeight', 'totalPrice']:
            if field in deliveryReturnData and isinstance(deliveryReturnData[field], float) and deliveryReturnData[field].is_integer():
                deliveryReturnData[field] = int(deliveryReturnData[field])

        if 'returnedItems' in deliveryReturnData and isinstance(deliveryReturnData['returnedItems'], list):
            for item in deliveryReturnData['returnedItems']:
                if isinstance(item, dict):
                    for item_field in ['total', 'unitPrice', 'weight']: # Assuming quantity is already int
                        if item_field in item and isinstance(item[item_field], float) and item[item_field].is_integer():
                            item[item_field] = int(item[item_field])
        
        # Convert timestamp fields to WIB
        timestamp_fields = ["returnDate"] # Add other timestamp fields if any
        for field in timestamp_fields:
            if field in deliveryReturnData and deliveryReturnData[field]:
                # Assuming convert_utc_to_wib returns a datetime object
                deliveryReturnData[field] = convert_utc_to_wib(deliveryReturnData[field]).isoformat()

        return {
            "status": "success",
            "message": f"Berhasil mendapatkan detail pengembalian paket '{orderNo}'",
            "data": deliveryReturnData
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during get return delivery detail for '{orderNo}': {str(e)}")
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
import urllib
from urllib.parse import unquote
from app.config.firestore import db
from fastapi import HTTPException
from datetime import datetime, timezone
from app.models.deliveryModel import packageDeliveryModel
from app.utils.location import getPackageLocation
from app.utils.time import convert_utc_to_wib

# ADD Package to packageCollection
async def addPackage(packageDataInput, currentUser):
    try:
        # Check if user is admin
        if currentUser["role"] not in ["admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "status": "fail",
                    "message": "Anda tidak memiliki akses untuk menambahkan order.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        orderData = packageDataInput.dict()

        # firestore does not allow / in document names
        orderNoFilered = orderData["orderNo"].replace("/", "_")
        
        # Check if orderNo already exists
        orderDoc = (
            db.collection("packageOrderCollection")
            .document(orderNoFilered)
            .get()
        )
        if orderDoc.exists:
            raise HTTPException(
                status_code=409,
                detail={
                    "status": "fail",
                    "message": f"Order dengan nomor '{orderData['orderNo']}' sudah ada",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )

        # generate maps url 
        if not orderData.get("addressMapUrl"):
            encodedAddress = urllib.parse.quote(orderData["address"])
            orderData["addressMapUrl"] = f"https://www.google.com/maps/search/?api=1&query={encodedAddress}"

        # add list items name to orderData 
        itemsList = [item["name"] for item in orderData["items"]]
        orderData.update ({"itemsList": itemsList})

        # Create a copy without items for the main document
        orderData_without_items = orderData.copy()
        orderData_without_items.pop("items", None)        

        db.collection("packageOrderCollection").document(orderNoFilered).set(orderData_without_items)
        
        # add each item to the items subcollection
        items_collection = db.collection("packageOrderCollection").document(orderNoFilered).collection("items")
        for i, item in enumerate(orderData["items"]):
            item_doc_id = f"item_{i+1}"
            items_collection.document(item_doc_id).set(item)
        
        orderData.update({
            "orderDate": convert_utc_to_wib(orderData["orderDate"])
        })

        return {
            "status": "success",
            "message": "Order berhasil ditambahkan",
            "data": orderData 
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# get detail package from packageOrderCollection
async def getPackageDetail(orderNo):
    try:
        # decode url 
        orderNo = unquote(orderNo)

        # firestore not allow / in document names
        orderNoFiltered = orderNo.replace("/", "_")
        
        packageDoc = ( 
            db.collection("packageOrderCollection")
            .document(orderNoFiltered)
            .get()
        )
        if not packageDoc.exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{orderNo}' tidak ditemukan.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
        packageData = packageDoc.to_dict()
        packageData["orderNo"] = orderNo

        # get the items subcollection
        items_collection = (
            db.collection("packageOrderCollection")
            .document(orderNoFiltered)
            .collection("items")
            .stream()
        )
        
        # items_list = []
        # for item_doc in items_collection:
        #     items_list.append(item_doc.to_dict())
        items_list = [item_doc.to_dict() for item_doc in items_collection]
        packageData["items"] = items_list                      
        
        packageData.update({
            "orderDate": convert_utc_to_wib(packageData["orderDate"]),
        })
        
        return {
            "status": "success",
            "message": "Berhasil mendapatkan detail paket",
            "data": packageData
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


# GET all packages from packageDeliveryCollection
async def getAllPackages():
    # db = get_db()
    packageDeliveryRef = db.collection("packageOrderCollection")
    packageDeliveryDocs = packageDeliveryRef.stream()
    packageList = []
    for package in packageDeliveryDocs:
        packageList.append(package.to_dict())
    return {
        "status": "success",
        "message": "Berhasil mendapatkan semua order paket",
        "data": packageList
    }
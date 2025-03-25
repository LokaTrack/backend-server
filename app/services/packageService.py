from app.config.firestore import get_db
from fastapi import HTTPException
from datetime import datetime
from app.models.packageModel import packageModel, packageDeliveryModel
from app.utils.location import getPackageLocation
from uuid import uuid4

# ADD Package to packageCollection
async def addPackage(packageDataInput):
    try:
        db = get_db()
        newPackageData= packageDataInput.dict()

        db.collection("packageCollection").document(newPackageData["packageId"]).set(newPackageData)
        return {
            "status": "success",
            "message": "Paket berhasil ditambahkan",
            "data": newPackageData
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

# ADD Package to packageDeliveryCollection and Change status to delivery
async def startDeliveryPackage(packageDataInput):
    try:
        db = get_db()
        # Check if package exists
        packageDoc = db.collection("packageCollection").document(packageDataInput.packageId).get()
        if not packageDoc.exists: 
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{packageDataInput.packageId}' tidak ditemukan.",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # if package status is already in in transit
        packageDeliveryDoc = db.collection("packageDeliveryCollection").document(packageDataInput.packageId).get()
        if packageDeliveryDoc.exists:
            packageDeliveryData = packageDeliveryDoc.to_dict()
            if packageDeliveryData["deliveryStatus"] == "in transit":
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "fail",
                        "message": f"Paket dengan id '{packageDataInput.packageId}' sudah dalam status 'in transit'.",
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        # get package location
        packageLocation = await getPackageLocation(packageDataInput.trackerId)
        packageDataInput.deliveryStartLocation = packageLocation

        # Add package to delivery collection
        newPackageData= packageDataInput.dict()
        newPackageData["deliveryStatus"] = "in transit"
        db.collection("packageDeliveryCollection").document(newPackageData["packageId"]).set(newPackageData)

        return {
            "status": "success",
            "message": "Paket berhasil ditambahkan ke delivery",
            "data": newPackageData
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )



# ADD Package to packageCollection
async def addPackageDUMMY():
    try:
        db = get_db()
        # Dummy Data
        newPackageDataDummy = packageModel(
            packageId = str(uuid4()),
            recipientName="John Doe",
            recipientNumber=123456789,
            recipientAddress="Jl. Jend. Sudirman No. 1, Jakarta",

            packageWeight=2.5,        
            packageDimension={
                "length": 10.0,
                "width": 5.0,
                "height": 5.0
            },
            additionalNotes="Fragile, Handle with care"
        )

        newPackageData= newPackageDataDummy.dict()
        db.collection("packageCollection").document(newPackageData["packageId"]).set(newPackageData)
        return {
            "status": "success",
            "message": "Paket berhasil ditambahkan",
            "data": newPackageData
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

async def startDeliveryPackageDUMMY(packageDataInput):
    try:
        db = get_db()
        packageCollection = db.collection("packageCollection")
        packageDoc = packageCollection.document(packageDataInput.packageId).get()
       
        if not packageDoc.exists: 
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "fail",
                    "message": f"Paket dengan id '{packageDataInput.packageId}' tidak ditemukan.",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Dummy Data
        newPackageDataDummy = packageDeliveryModel(
            packageId = packageDataInput.packageId,
            driverId = str(uuid4()),
            trackerId = "Ue2KlB6IMPdfoBN4CR2b",
            deliveryStatus = "in transit",
            deliveryStartLocation={
                "latitude": 12.0,
                "longitude": 16
            },
            deliveryStartTime=datetime.now()
        )
        # <-- end of dummy data -->

        newPackageData = newPackageDataDummy.dict()
        db.collection("packageDeliveryCollection").document(newPackageData["packageId"]).set(newPackageData)

        return {
            "status": "success",
            "message": "Paket berhasil ditambahkan ke delivery",
            "data": newPackageData
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )



# GET all packages from packageDeliveryCollection
async def getAllPackages():
    db = get_db()
    packageDeliveryCollection = db.collection("packageDeliveryCollection")
    allPackages = packageDeliveryCollection.stream()
    packageList = []
    for package in allPackages:
        packageList.append(package.to_dict())
    return {
        "status": "success",
        "message": "Berhasil mendapatkan semua paket",
        "data": packageList
    }
from app.config.firestore import db
from app.utils.time import convert_utc_to_wib, get_wib_day_range
from google.cloud.firestore import FieldFilter
from fastapi import HTTPException
from datetime import datetime, timezone
import logging
logger = logging.getLogger(__name__)

async def getDashboard (currentUser):
    """Get user dashboard data"""
    try: 
        today_start, today_end = get_wib_day_range()
        # today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # today_end = today_start + timedelta(days=1) - timedelta(seconds=1)
        
        # statistic 
        onDeliveredPackages = 0
        checkedInPackages = 0
        deliveredPackages = 0
        returnedPackages = 0
        others = 0
        totalDeliveries = 0
        percentage =  0

        deliveryDocs = (
            db.collection("packageDeliveryCollection")
            .where(filter=FieldFilter("driverId", "==", currentUser["userId"]))
            .where(filter=FieldFilter("deliveryStartTime", ">=", today_start))
            # .where("deliveryStartTime", "<=", today_end)
            .get()
        )

        if not deliveryDocs:
            return {
                "status": "success",
                "message": f"Tidak ada data pengiriman hari ini untuk user '{currentUser['username']}'.",
                "data": {
                    "onDeliveredPackages": 0,
                    "checkedInPackages": 0,
                    "deliveredPackages": 0,
                    "returnedPackages": 0,
                    "others": 0,
                    "percentage ": 0,
                    "recentOrder": []
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }    
        recentOrder = [deliveryDoc.to_dict() for deliveryDoc in deliveryDocs]
        totalDeliveries = len(recentOrder)

        # for x in recentOrder :
        #     if x.get("deliveryStatus") == "dikirim":
        #         statistics["dikirim"] += 1
        #     elif x.get("deliveryStatus") == "sampai":
        #         statistics["sampai"] += 1
        #     elif x.get("deliveryStatus") == "diterima":
        #         statistics["diterima"] += 1
        #     elif x.get("deliveryStatus") == "dikembalikan":
        #         statistics["dikembalikan"] += 1
        #     else :
        #         statistics["others"] += 1


        for x in recentOrder:
            status = x.get("deliveryStatus")
            if status == "On Delivery":
                onDeliveredPackages += 1
            elif status == "Check-in":
                checkedInPackages += 1
            elif status == "Check-out":
                deliveredPackages += 1
            elif status == "Return":
                returnedPackages += 1
            else:
                others += 1

        if totalDeliveries > 0:
            # Consider both selesai and dikembalikan as completed
            completed = deliveredPackages + returnedPackages
            percentage = int((completed / totalDeliveries) * 100)

        # convert all timestamps in response to WIB
        for order in recentOrder:
            for time_field in ["deliveryStartTime", "checkInTime", "checkOutTime", "returnTime", "lastUpdateTime"]:
                if time_field in order and order[time_field]:
                    order[time_field] = convert_utc_to_wib(order[time_field]).isoformat()
        
        data = {
                "onDeliveredPackages": onDeliveredPackages,
                "checkedInPackages": checkedInPackages,
                "deliveredPackages": deliveredPackages,
                "returnedPackages": returnedPackages,
                "totalDeliveries": totalDeliveries,
                "others": others,
                "percentage": percentage,
                "recentOrder": recentOrder,
        }
        return {
            "status": "success",
            "message": "Mengambil data dashboard berhasil",
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e   :
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

async def getHistory (currentUser):
    """Get User History Data"""
    try:
        # statistic
        deliveredPackages = 0
        returnedPackages = 0
        totalDeliveries = 0

        historyDocs = (
            db.collection("packageDeliveryCollection")
            .where(filter=FieldFilter("driverId", "==", currentUser["userId"]))
            .where(filter=FieldFilter("deliveryStatus", "in", ["Check-out", "Return"]))
            .get()
        )
        if not historyDocs:
            return {
                "status": "success",
                "message": f"Tidak ada data pengiriman untuk user '{currentUser['username']}'.",
                "data": { 
                    "deliveredPackages" : 0,
                    "returnedPackages" : 0,
                    "totalDeliveries": 0,   
                    "history": [] 
                    },
                "timestamp": convert_utc_to_wib(datetime.now(timezone.utc).isoformat())
            }
        
        # for history in historyDocs :
        #     historyData = history.to_dict()
        #     print ("/n ", historyData)
        #     if historyData.get("deliveryStatus") == "Check-out" :
        #         print ("\n append to Check-out : ", historyData)
        #         historyDelivery.append(historyData)
        #         statistics["Check-out"] += 1
        #     elif historyData.get("deliveryStatus") == "Return" :
        #         print ("\n  append to Return : ", historyData)
        #         historyDelivery.append(historyData)
        #         statistics["Return"] += 1

        historyDeliveries = []
        for history in historyDocs:
            historyData = history.to_dict()
            historyDeliveries.append(historyData)
            status = historyData.get("deliveryStatus")
            
            # Add statistics 
            if status == "Check-out":
                deliveredPackages += 1
            elif status == "Return":
                returnedPackages += 1

            # convert all timestamps in response to WIB
            timestamp_fields = ["checkInTime", "checkOutTime", "deliveryStartTime", "lastUpdateTime", "returnTime", "timestamp"]
            for field in timestamp_fields:
                if field in historyData and historyData[field]:
                    historyData[field] = convert_utc_to_wib(historyData[field]).isoformat()
        
        totalDeliveries = len (historyDeliveries)

        data = {
            "deliveredPackages": deliveredPackages,
            "returnedPackages": returnedPackages,
            "totalDeliveries": totalDeliveries,
            "history" : historyDeliveries,
        }
        return {
            "status": "success",
            "message": "Mengambil data history berhasil",
            "data": data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while fetching history for user {currentUser['userId']}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    

async def getDeliveries (currentUser) :
    """Get all user's delivery"""
    try : 
        deliveries = []
        deliveryDocs = (
            db.collection("packageDeliveryCollection")
            .where(filter=FieldFilter("driverId", "==", currentUser["userId"]))
            .order_by("lastUpdateTime", direction="DESCENDING")
            .stream()
        )
        if not deliveryDocs:
            return {
                "status": "success",
                "message": f"Tidak ada data pengiriman untuk user '{currentUser['username']}'.",
                "data": {
                    "deliveries": []
                },
            }


        for deliveryDoc in deliveryDocs: 
            deliveryData = deliveryDoc.to_dict()
            # convert all timestamps in response to WIB
            timestamp_fields = ["deliveryStartTime", "checkInTime", "checkOutTime", "returnTime", "lastUpdateTime"]
            for field in timestamp_fields:
                if field in deliveryData and deliveryData[field]:
                    deliveryData[field] = convert_utc_to_wib(deliveryData[field]).isoformat()
            
            deliveries.append(deliveryData)

        return {
            "status": "success",
            "message": "Mengambil data pengiriman berhasil",
            "data": {
                "deliveries": deliveries
            }   
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving delivery packages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "fail",
                "message": f"Terjadi kesalahan: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
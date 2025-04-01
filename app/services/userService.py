from app.config.firestore import db
from app.utils.time import convert_utc_to_wib, get_wib_day_range
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
        statistics = {
            "delivery": 0,
            "checkin": 0,
            "checkout": 0,
            "return": 0,
            "others": 0,
            "percentage" : 0
        }

        deliveryDocs = (
            db.collection("packageDeliveryCollection")
            .where("driverId", "==", currentUser["userId"])
            .where("deliveryStartTime", ">=", today_start)
            # .where("deliveryStartTime", "<=", today_end)
            .get()
        )

        if not deliveryDocs:
            return {
                "status": "success",
                "message": f"Tidak ada data pengiriman hari ini untuk user '{currentUser['username']}'.",
                "data": {
                    "statistics": statistics,
                    "recentOrder": []
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }    
        recentOrder = [deliveryDoc.to_dict() for deliveryDoc in deliveryDocs]
        totalPackage = len(recentOrder)
        statistics["totalPackage"] = totalPackage

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

        status_mapping = {
            "delivery": "delivery", 
            "checkin": "checkin", 
            "checkout": "checkout", 
            "return": "return"
        }

        for x in recentOrder:
            key = status_mapping.get(x.get("deliveryStatus"), "others")
            statistics[key] += 1

        if totalPackage > 0:
            # Consider both selesai and dikembalikan as completed
            completed = statistics["checkout"] + statistics["return"]
            statistics["percentage"] = int((completed / totalPackage) * 100)

        # convert all timestamps in response to WIB
        for order in recentOrder:
            for time_field in ["deliveryStartTime", "checkInTime", "checkOutTime", "returnTime", "lastUpdateTime"]:
                if time_field in order and order[time_field]:
                    order[time_field] = convert_utc_to_wib(order[time_field]).isoformat()
        
        data = {
                "statistics" : statistics,
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
        historyDelivery = []
        statistics = {
            "success": 0,
            "return": 0,
            "totalDelivery": 0,
        }
        historyDocs = (
            db.collection("packageDeliveryCollection")
            .where("driverId", "==", currentUser["userId"])
            .get()
        )
        if not historyDocs:
            return {
                "status": "success",
                "message": f"Tidak ada data pengiriman untuk user '{currentUser['username']}'.",
                "data": { "statistics": statistics, "history": [] },
                "timestamp": convert_utc_to_wib(datetime.now(timezone.utc).isoformat())
            }
        
        # for history in historyDocs :
        #     historyData = history.to_dict()
        #     print ("/n ", historyData)
        #     if historyData.get("deliveryStatus") == "checkout" :
        #         print ("\n append to checkout : ", historyData)
        #         historyDelivery.append(historyData)
        #         statistics["checkout"] += 1
        #     elif historyData.get("deliveryStatus") == "return" :
        #         print ("\n  append to return : ", historyData)
        #         historyDelivery.append(historyData)
        #         statistics["return"] += 1
        status_mapping = {
            "checkout": "success",
            "return": "return"
        }

        for history in historyDocs:
            historyData = history.to_dict()
            status = historyData.get("deliveryStatus")
            if status in status_mapping:
                historyDelivery.append(historyData)
                statistics[status_mapping[status]] += 1
                # convert all timestamps in response to WIB
                timestamp_fields = ["checkInTime", "checkOutTime", "deliveryStartTime", "lastUpdateTime", "returnTime", "timestamp"]
                for field in timestamp_fields:
                    if field in historyData and historyData[field]:
                        historyData[field] = convert_utc_to_wib(historyData[field]).isoformat()
        
        statistics["totalDelivery"] = len (historyDelivery)

        data = {
            "statistics" : statistics,
            "history" : historyDelivery,
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
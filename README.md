# LokaTrack - API and Deployment

This is the backend API for the LokaTrack project. The API serves as the backend for the mobile application, providing endpoints to manage package statuses, track locations, and handle other related functionalities. The backend is built using **FastAPI** and is designed to integrate seamlessly with IoT devices and GPS trackers.

## Features
- **Package Management**: Update and retrieve package statuses, including delivery and return processes.
- **Location Tracking**: Receive and store GPS data from IoT devices for real-time tracking.
- **Return Package Handling**: Support for managing returned packages.
- **Mobile Integration**: Provide APIs for mobile applications to interact with the backend.

## Database Structure
```
TrackerCollection  →  IoT Tracker (Perangkat GPS yang digunakan untuk tracking)
 ├── {trackerId} (Document)
 │   ├── trackerName: "IoT GPS Device A"
 │   ├── registrationDate: "2025-01-01"
 │   ├── latitude: -6.2088
 │   ├── longitude: 106.8456
 │   ├── lastUpdated: "2025-03-22T10:30:00Z"

userCollection  →  Data Pengguna (Driver & Admin)
 ├── {user_id} (Document)
 │   ├── username: "John Doe"
 │   ├── role: "driver"  (driver | admin)
 │   ├── email: "john@example.com"
 │   ├── hashedPassword: "xxxxxxxxx"
 │   ├── phoneNumber: "08123456789" (Optional)
 │   ├── registrationDate: "2025-01-01"
 │   ├── trackerId: "xxxxx"

 packageOrderCollection (Collection)
 ├── {orderNo} (Document)
 │   ├── orderDate: "12/2/2025"
 │   ├── orderNo: "OB/03-2025/129"
 │   ├── costumer: "dony"
 │   ├── address: "123 Main Street, Jakarta"
 │   ├── addressMapUrl: "https://www.google.com/maps/search/?api=1 query=123%20Main%20Street%20,%20Jakarta"
 │   ├── phone: "0812312xxxx"
 │   ├── items (Sub-collection)
 │   │    📄 item_1
 │   │    │   ├── name: "Brokoli Gundul (0.5 Kg)"
 │   │    │   ├── weight: 0.5 
 │   │    │   ├── quantity: 5
 │   │    │   ├── unitPrice: 57000
 │   │    │   ├── total: 285000
 │   │    │   ├── notes: ""
 │   │    📄 item_2
 │   │    │   ├── name: "Caisim (0.1 Kg)"
 │   │    │   ├── weight: 0.1
 │   │    │   ├── quantity: 2
 │   │    │   ├── unitPrice: 31500
 │   │    │   ├── total: 63000
 │   │    │   ├── notes: ""
 │   ├── totalWeight: 2.7
 │   ├── subTotal: 1238575
 │   ├── discount: 0
 │   ├── shipping: 0
 │   ├── totalPrice: 1238575

 packageDeliveryCollection  →  Data Paket & Status Pengiriman
 ├── {orderNo} (Document)
 │   ├── orderNo: "OB/03-2025/129"
 │   ├── driverId: "user_123"
 │   ├── costumer: "dony"
 │   ├── address: "123 Main Street, Jakarta"
 │   ├── totalWeight: 2.7
 │   ├── totalPrice: 1238575
 │   ├── deliveryStatus: "dikirim"
 │   ├── trackerId: "1231xxxx"
 │   ├── deliveryStartTime: "2025-03-22T08:00:00Z"
 |   ├── checkInTime: ""
 |   ├── checkOutTime: ""
 |   ├── lastUpdateTime: ""


returnPackageCollection (Collection)
 ├── {returnOrderNo} (Document)
 │   ├── previousPackageId: "PKG123"
 │   ├── previousDriverId: "user_123"
 │   ├── newDriverId: "user_456"
 │   ├── returnStartTime: "2025-03-22T12:00:00Z"
 │   ├── returnStartLocation: { 
 │   |          latitude: -6.2120, 
 │   |          longitude: 106.8485 
 │   |      }
 │   ├── returnEndTime: "2025-03-22T13:30:00Z"
 │   ├── returnEndLocation: { 
 │   |          latitude: -6.2150, 
 │   |          longitude: 106.8500 
 │   |      }
 ```


## API Response Format
### Success Response
```json
{
    "status": "success",
    "message": "xxxx successfully executed",
}
```

### Success Response with Detail
```json
{
    "status": "success",
    "message": "xxxx successfully executed",
    "data": {
        "xxxx"
    }
}
```

### Failure Response
```json
{
    "status": "fail",
    "message": "xxx failed to execute",
    "timestamp": "xxxxx"
}
```

### Failure Response with Error Details
```json
{
    "status": "fail",
    "message": "xxx failed to execute",
    "timestamp": "xxxxx",
    "errors": {
        "field": "name",
        "issue": "Name is required"
    }
}
```


## How to Run
1. Clone the repository:
   ```bash
   git clone https://github.com/username/project-kekhususan-backend.git
   ```
2. Navigate to the project directory:
   ```bash
   cd project-kekhususan-backend
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```


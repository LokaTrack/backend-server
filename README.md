# LokaTrack - API and Deployment

This is the backend API for the LokaTrack project. The API serves as the backend for the mobile application, providing endpoints to manage package statuses, track locations, and handle other related functionalities. The backend is built using **FastAPI** and is designed to integrate seamlessly with IoT devices and GPS trackers.

## Features
- **Package Management**: Update and retrieve package statuses, including delivery and return processes.
- **Location Tracking**: Receive and store GPS data from IoT devices for real-time tracking.
- **Return Package Handling**: Support for managing returned packages.
- **Mobile Integration**: Provide APIs for mobile applications to interact with the backend.

## Database Structure
```json
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

 packageCollection  →  Data Paket & Status Pengiriman
 ├── {packageId} (Document)
 │   ├── driverId: "user_123"
 │   ├── status: "in_transit"
 │   ├── trackerId: "tracker_01"
 │   ├── deliveryStartTime: "2025-03-22T08:00:00Z"
 │   ├── deliveryStartLocation: { 
                latitude: -6.2088, 
                longitude: 106.8456 
            }
 │   ├── checkinTime: "2025-03-22T09:30:00Z"
 │   ├── checkinLocation: { 
                latitude: -6.2095, 
                longitude: 106.8460 
            }
 │   ├── checkoutTime: "2025-03-22T10:45:00Z"
 │   ├── checkoutLocation: { 
                latitude: -6.2102, 
                longitude: 106.8472 
            }

returnPackageCollection (Collection)
 ├── {returnPackageId} (Document)
 │   ├── previousPackageId: "PKG123"
 │   ├── previousDriverId: "user_123"
 │   ├── newDriverId: "user_456"
 │   ├── returnStartTime: "2025-03-22T12:00:00Z"
 │   ├── returnStartLocation: { 
                latitude: -6.2120, 
                longitude: 106.8485 
            }
 │   ├── returnEndTime: "2025-03-22T13:30:00Z"
 │   ├── returnEndLocation: { 
                latitude: -6.2150, 
                longitude: 106.8500 
            }
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
   uvicorn main:app --reload
   ```



# API Specification

This document provides the specifications for the API endpoints of our application. Each endpoint is described with its URL, HTTP method, request parameters, and possible responses. The API is designed to be RESTful and follows standard conventions for request and response formats.


# Authentication Endpoints
## 1. Register Process
- URL
  - `/api/v1/register`
- Method
  - `POST`
- Request Body :
  - `email` as `string`, must be `unique`
  - `username` as string
  - `password` as `string`, must be at least 8 characters
  - `passwordConfirmation` as `string`, must be same as password

#### Success
Success  (Status code 201) :
```json
{
  "status": "success",
  "message": "Akun anda berhasil dibuat!"
}
```

#### Failure
if fail - email already taken (Status code 400):
```json
{
  "status": "fail",
  "message": "Email ini sudah digunakan",
  "timestamp": "xxxxxx"
}
```

if fail - password less than 8 character (Status code 400):
```json
{
  "status": "fail",
  "message": "Password harus memiliki minimal 8 karakter",
  "timestamp": "xxxxxx"
}
```

if fail - password and password confirmation not same (Status code 400):
```json
{
  "status": "fail",
  "message": "Password dan password konfirmasi tidak sama",
  "timestamp": "xxxxxx"
}
```


## 2. Login
- URL
  - `/api/v1/login`
- Method
  - `POST`
- Request Body
  - `email` as `string`
  - `password` as `string`


#### Success
Success  (Status code 200) :
```json
{
  "status": "success",
  "message": "Login berhasil",
  "data": {
    "email": "useerer@exampleee.com",
    "username": "John",
    "role": "driver",
    "token": "xxxxx"
  }
}
```

#### Failure
if fail - wrong email or password (Status code 401)
```json
{
  "status": "fail",
  "message": "Email atau password salah",
  "timestamp": "xxxxxx"
}
```

# User Profile Endpoints

## 1. Get User Profile 
Get current user profile information
- URL
  - `/api/v1/profile`

- Method
  - `GET`

- Headers
  - `Authorization: Bearer <token>`

### Success
```json
{
    "status": "success",
    "data": {
        "phoneNumber": null,
        "userId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
        "emailVerified": false,
        "role": "driver",
        "registrationDate": "2025-03-27T08:08:19.457710+00:00",
        "email": "xxxx@lokatrack.com",
        "username": "John Doe"
    }
}
```

## 2. Update Username
- URL
  - `/api/v1/profile/username`

- Method
  - `PUT`

- Request Body
  - `username` as `string`

### Sucess
```json
{
  "status": "success",
  "message": "username berhasil diubah",
}
```

### Failure
```json
{
  "status": "fail",
  "message": "Update username gagal",
  "timestamp": "2025-03-28T12:00:00.000000"
}
```

## 3. Update Phone Number
- URL
  - `/api/v1/profile/phone-number`

- Method
  - `PUT`

- Request Body
  - `phoneNumber` as `string`

### Success
```json
{
  "status": "success",
  "message": "Nomor telepo berhasil diubah",
}
```

### Failure
```json
{
  "status": "fail",
  "message": "Update nomor telepon gagal",
  "timestamp": "2025-03-28T12:00:00.000000"
}
```


## 4. Update password
- URL
  - `/api/v1/profile/password`

- Method
  - `PUT`

- Request Body
  - `currentPassword` as `string`
  - `newPassword` as `string`
  - `passwordConfirmation` as `string`

### Success
```json
{
  "status": "success",
  "message": "password berhasil diubah",
}
```

### Failure
if fail - Incorrect current password (400 Bad Request)
```json
{
  "status": "fail",
  "message": "Password lama anda salah",
  "timestamp": "2025-03-28T12:00:00.000000"
}
```
if fail - New password same as old (400 Bad Request)
```json
{
  "status": "fail",
  "message": "Password baru tidak boleh sama dengan password lama",
  "timestamp": "2025-03-28T12:00:00.000000"
}
```

if fail - Password confirmation mismatch (400 Bad Request)
```json
{
  "status": "fail",
  "message": "Password baru dan konfirmasi password tidak sama",
  "timestamp": "2025-03-28T12:00:00.000000"
}
```

if fail - Password too short (400 Bad Request)
```json
{
  "status": "fail",
  "message": "Password baru harus memiliki minimal 8 karakter",
  "timestamp": "2025-03-28T12:00:00.000000"
}
```

## 5. Update Profile Picture
- URL
  - `/api/v1/profile/profile-picture`

- Method
  - `PUT`

- Request Body form data
  - `profilePicture` as `string`




# Package Endpoint
## 1. Add Package
- URL
  - `/api/v1/package/add`

- Method
  - `POST`

- Headers
  - `Authorization: Bearer <token>`

- Request Body:
  - `orderNo` as `string`, must be unique
  - `orderDate` as `datetime` (optional, default = current time)
  - `customer` as `string`
  - `address` as `string`
  - `addressMapUrl` as `string` (optional)
  - `phone` as `string`
  - `items` as array of objects:
      - `name` as `string`
      - `quantity` as `integer`
      - `unitPrice` as `float`
      - `total` as `float` (should equal quantity * unitPrice)
      - `notes` as `string` (optional)
      - `weight` as `float` (per item in kg)
  - `totalWeight` as `float` (in kg, should equal sum of item weights)
  - `subTotal` as `float` (should equal sum of item totals)
  - `discount` as `float` (default = 0)
  - `shipping` as `float` (default = 0)
  - `totalPrice` as `float` (should equal subTotal - discount + shipping)
  - `orderNotes` as `string` (optional)

### Success
Success (Status code 201):
```json
{
    "status": "success",
    "message": "Order berhasil ditambahkan",
    "data": {
        "orderNo": "OB/01-2025/24",
        "orderDate": "2025-04-03T18:13:16.964637+07:00",
        "customer": "John Doe",
        "address": "123 Main Street, Central Jakarta",
        "addressMapUrl": "https://www.google.com/maps/search/?api=1&query=123%20Main%20Street%2C%20Central%20Jakarta",
        "phone": "081234567890",
        "items": [
            {
                "name": "Sayur Bayam",
                "quantity": 4,
                "unitPrice": 14000.0,
                "total": 56000.0,
                "notes": "",
                "weight": 0.5
            },
            {
                "name": "Brokoli Gundul",
                "quantity": 5,
                "unitPrice": 30000.0,
                "total": 150000.0,
                "notes": "",
                "weight": 1.0
            },
            {
                "name": "Cabai Merah",
                "quantity": 4,
                "unitPrice": 60000.0,
                "total": 240000.0,
                "notes": "",
                "weight": 1.0
            }
        ],
        "totalWeight": 11.0,
        "subTotal": 446000.0,
        "discount": 0.0,
        "shipping": 0.0,
        "totalPrice": 446000.0,
        "orderNotes": "Pastikan cabai nya segar",
        "itemsList": [
            "Sayur Bayar",
            "Brokoli Gundul",
            "Cabai Merah"
        ]
    }
}
```

### Failure
If fail - unauthorized (Status code 403):
```json
{
  "status": "fail",
  "message": "Anda tidak memiliki akses untuk menambahkan order.",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

If fail - order already exists (Status code 409):
```json
{
  "status": "fail",
  "message": "Order dengan nomor 'OB/03-2025/129' sudah ada",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

If fail - internal error (Status code 500):
```json
{
  "status": "fail",
  "message": "Terjadi kesalahan: [error details]",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

## 2. Get Package Detail
- URL
  - `/api/v1/packages/{orderNo}`

- Method
  - `GET`

- Header 
  - `Authorization: Bearer <token>`

- Path Parameters:
  - `orderNo` as `string`
  - **Note**: The `orderNo` must be DOUBLE URL-encoded, example:   
    - Original order number: `OB/01-2025/19129`
    - Single-encoded (NOT WORKING): `OB%2F01-2025%2F19129`
    - Double-encoded (CORRECT): `OB%252F01-2025%252F19129`

### success
Success (Status code 200):
```json
{
    "status": "success",
    "message": "Berhasil mendapatkan detail paket",
    "data": {
        "orderNo": "OB/01-2025/24",
        "orderDate": "2025-04-03T18:13:16.964637+07:00",
        "itemsList": [
            "Sayur Bayar",
            "Brokoli Gundul",
            "Cabai Meram"
        ],
        "phone": "081234567890",
        "discount": 0.0,
        "totalWeight": 11.0,
        "customer": "John Doe",
        "addressMapUrl": "https://www.google.com/maps/search/?api=1&query=123%20Main%20Street%2C%20Central%20Jakarta",
        "subTotal": 446000.0,
        "address": "123 Main Street, Central Jakarta",
        "orderNotes": "Pastikan cabai nya segar",
        "totalPrice": 446000.0,
        "shipping": 0.0,
        "items": [
            {
                "weight": 0.5,
                "notes": "",
                "unitPrice": 14000.0,
                "total": 56000.0,
                "quantity": 4,
                "name": "Sayur Bayam"
            },
            {
                "weight": 1.0,
                "notes": "",
                "unitPrice": 30000.0,
                "total": 150000.0,
                "quantity": 5,
                "name": "Brokoli Gundul"
            },
            {
                "weight": 1.0,
                "notes": "",
                "unitPrice": 60000.0,
                "total": 240000.0,
                "quantity": 4,
                "name": "Cabai Merah"
            }
        ]
    }
}
```

### Failure

If fail - package not found (Status code 404):
```json
{
  "status": "fail",
  "message": "Paket dengan id 'OB/03-2025/129' tidak ditemukan.",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

If fail - internal error (Status code 500):
```json
{
  "status": "fail",
  "message": "Terjadi kesalahan: [error details]",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

# Delivery Endpoints
## 1. Start Delivery Package
Start delivery process for a package
- URL
  - `/api/v1/delivery`

- Method
  - `POST`
- Header 
  - `Authorization: Bearer <token>`

- Request Body:
  - `orderNo` as `string`, must exist in packageOrderCollection

### Success
Success (Status code 201):
```json
{
    "status": "success",
    "message": "Paket berhasil ditambahkan ke delivery",
    "data": {
        "orderNo": "OB/01-2025/24",
        "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
        "customer": "John Doe",
        "address": "123 Main Street, Central Jakarta",
        "itemsList": [
            "Sayur Bayam",
            "Brokoli Gundul",
            "Cabai Merah"
        ],
        "totalWeight": 11.0,
        "totalPrice": 446000.0,
        "deliveryStatus": "On Delivery",
        "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
        "deliveryStartTime": "2025-04-03T18:14:32.592510+07:00",
        "checkInTime": null,
        "checkOutTime": null,
        "lastUpdateTime": "2025-04-03T18:14:32.592510+07:00",
        "orderNotes": "Pastikan cabai nya segar"
    }
}
```

### Failure
If fail - package not found (Status code 404):
```json
{
  "status": "fail",
  "message": "Paket dengan id 'PKG12345' tidak ditemukan.",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```
 (Status code 400):
```json
{
  "status": "fail",
  "message": "Paket dengan id 'ORD-12345' sudah dalam status 'dikirim'.",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

If fail - internal error (Status code 500):
```json
{
  "status": "fail",
  "message": "Terjadi kesalahan: [error details]",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

## 2. Update Delivery Status
Updates the delivery status of a package. The status must follow the valid transition rules:
> On Deliveery → Check-in → Check-out → Return


- URL
  - `/api/v1/delivery`

- Method
  - `PUT`

- Header 
  - `Authorization: Bearer <token>`

- Request Body:
  - `orderNo` as `string`, 
  - `deliveryStatus` as string
    > Possible values: "On Delivery", "Check-in", "Check-out", "Return"

### Success
```json
{
    "status": "success",
    "message": "Status paket 'OB/01-2025/24' berhasil diupdate",
    "data": {
        "orderNo": "OB/01-2025/24",
        "deliveryStatus": "Check-in",
        "lastUpdateTime": "2025-04-03T18:19:36.097230+07:00",
        "totalWeight": 11.0,
        "checkOutTime": null,
        "totalPrice": 446000.0,
        "deliveryStartTime": "2025-04-03T18:14:32.592510+07:00",
        "orderNotes": "Pastikan cabai nya segar",
        "itemsList": [
            "Sayur Bayar",
            "Brokoli Gundul",
            "Cabai Merah"
        ],
        "checkInTime": "2025-04-03T18:19:36.097230+07:00",
        "customer": "John Doe",
        "address": "123 Main Street, Central Jakarta",
        "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
        "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302"
    }
}
```

### Fail
```json
{
    "status": "fail",
    "message": "Tidak bisa mengubah status paket dari 'checkout' menjadi 'delivery'.",
    "timestamp": "2025-03-31T03:24:06.140512"
}
```


## 3. Get Delivery Detail
  - `/api/v1/delivery/{orderNo}`

- Method
  - `GET`

- Header 
  - `Authorization: Bearer <token>`

- Path Parameters:
  - `orderNo` as `string`

**Note**: The `orderNo` must be DOUBLE URL-encoded, example:   
  - Original order number: `OB/01-2025/19129`
  - Single-encoded (NOT WORKING): `OB%2F01-2025%2F19129`
  - Double-encoded (CORRECT): `OB%252F01-2025%252F19129`

### Success
```json
{
    "status": "success",
    "message": "Mengambil data pengiriman berhasil",
    "data": {
        "orderNo": "OB/01-2025/24",
        "deliveryStatus": "On Delivery",
        "lastUpdateTime": "2025-04-03T18:14:32.592510+07:00",
        "totalWeight": 11.0,
        "checkOutTime": null,
        "totalPrice": 446000.0,
        "deliveryStartTime": "2025-04-03T18:14:32.592510+07:00",
        "orderNotes": "Pastikan cabai nya segar",
        "itemsList": "Sayur Bayam, Brokoli Gundul, Cabai Merah",
        "checkInTime": null,
        "customer": "John Doe",
        "address": "123 Main Street, Central Jakarta",
        "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
        "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302"
    }
}
```

# User Endpoint
## 1. Dashboard
- URL
  - `/api/v1/dashboard`

- Method
  - `GET`

- Header 
  - `Authorization: Bearer <token>`
  
```json
{
    "status": "success",
    "message": "Mengambil data dashboard berhasil",
    "data": {
        "statistics": {
            "dikirim": 3,
            "sampai": 1,
            "selesai": 1,
            "dikembalikan": 1,
            "others": 0,
            "percentage": 33,
            "totalPackage": 6
        },
        "recentOrder": [
            {
                "orderNo": "OB/01-2025/1",
                "deliveryStatus": "delivery",
                "checkInTime": null,
                "lastUpdateTime": "2025-03-27T16:48:00.956000+00:00",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T16:48:00.049000+00:00",
                "checkOutTime": null
            },
            {
                "orderNo": "OB/01-2025/2",
                "deliveryStatus": "return",
                "checkInTime": null,
                "lastUpdateTime": "2025-03-27T16:48:00.956000+00:00",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T16:48:00.121000+00:00",
                "checkOutTime": null
            },
            {
                "orderNo": "OB/01-2025/5",
                "deliveryStatus": "checkout",
                "checkInTime": null,
                "lastUpdateTime": "2025-03-27T16:48:00.956000+00:00",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T16:48:00.557000+00:00",
                "checkOutTime": null
            },
            {
                "orderNo": "OB/01-2025/2",
                "deliveryStatus": "delivery",
                "checkInTime": null,
                "lastUpdateTime": "2025-03-27T16:48:00.956000+00:00",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T16:48:00.575000+00:00",
                "checkOutTime": null
            },
            {
                "orderNo": "OB/01-2025/19129",
                "deliveryStatus": "delivery",
                "checkInTime": null,
                "lastUpdateTime": "2025-03-27T16:48:00.956517+00:00",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T16:48:00.672000+00:00",
                "checkOutTime": null
            },
            {
                "orderNo": "OB/01-2025/4",
                "deliveryStatus": "checkin",
                "checkInTime": null,
                "lastUpdateTime": "2025-03-27T16:48:00.956000+00:00",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T16:48:00.795000+00:00",
                "checkOutTime": null
            }
        ]
    }
}
```


## 2. History
- URL
  - `/api/v1/history`

- Method
  - `GET`

- Header 
  - `Authorization: Bearer <token>`

### Sucess
```json
{
    "status": "success",
    "message": "Mengambil data history berhasil",
    "data": {
        "statistics": {
            "success": 2,
            "return": 2,
            "totalDelivery": 4
        },
        "history": [
            {
                "orderNo": "OB/01-2025/1",
                "deliveryStatus": "checkout",
                "checkInTime": "2025-03-31T01:48:03.003743+00:00",
                "lastUpdateTime": "2025-03-31T01:48:03.003743+00:00",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T16:48:00.049000+00:00",
                "checkOutTime": "2025-03-31T01:48:03.003743+00:00"
            },
            {
                "orderNo": "OB/01-2025/104",
                "deliveryStatus": "return",
                "checkInTime": "2025-03-31T03:17:59.852427",
                "returnTime": "2025-03-31T03:37:24.011971",
                "lastUpdateTime": "2025-03-31T03:37:24.011971",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T15:00:54.307042+00:00",
                "checkOutTime": "2025-03-31T03:18:31.059068"
            },
            {
                "orderNo": "OB/01-2025/111",
                "deliveryStatus": "checkout",
                "checkInTime": "2025-03-31T01:48:03.003743+00:00",
                "lastUpdateTime": "2025-03-31T03:16:42.973812",
                "totalWeight": 6.7,
                "customer": "John Doe",
                "address": "123 Main Street, Central Jakarta",
                "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
                "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
                "totalPrice": 576000,
                "deliveryStartTime": "2025-03-30T20:02:22.314527+00:00",
                "checkOutTime": "2025-03-31T03:16:42.973812"
            },
        ]
    }
}
```
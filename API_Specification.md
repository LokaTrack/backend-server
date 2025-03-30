
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

### Success
Success (Status code 201):
```json
{
  "status": "success",
  "message": "Order berhasil ditambahkan",
  "data": {
    "orderNo": "OB/03-2025/129",
    "orderDate": "2025-03-25T21:30:00.000000",
    "customer": "John Doe",
    "address": "Jl. Jend. Sudirman No. 1, Jakarta",
    "addressMapUrl": "https://www.google.com/maps/search/?api=1&query=Jl.%20Jend.%20Sudirman%20No.%201%2C%20Jakarta",
    "phone": "081234567890",
    "items": [
      {
        "name": "Product A",
        "quantity": 2,
        "unitPrice": 50000,
        "total": 100000,
        "notes": "",
        "weight": 0.5
      },
      {
        "name": "Product B",
        "quantity": 1,
        "unitPrice": 75000,
        "total": 75000,
        "notes": "Fragile",
        "weight": 0.2
      }
    ],
    "totalWeight": 1.2,
    "subTotal": 175000,
    "discount": 10000,
    "shipping": 15000,
    "totalPrice": 180000
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
    "orderNo": "OB/03-2025/129",
    "orderDate": "2025-03-25T21:30:00.000000",
    "customer": "John Doe",
    "address": "Jl. Jend. Sudirman No. 1, Jakarta",
    "addressMapUrl": "https://www.google.com/maps/search/?api=1&query=Jl.%20Jend.%20Sudirman%20No.%201%2C%20Jakarta",
    "phone": "081234567890",
    "items": [
      {
        "name": "Product A",
        "quantity": 2,
        "unitPrice": 50000,
        "total": 100000,
        "notes": "",
        "weight": 0.5
      },
      {
        "name": "Product B",
        "quantity": 1,
        "unitPrice": 75000,
        "total": 75000,
        "notes": "Fragile",
        "weight": 0.2
      }
    ],
    "totalWeight": 1.2,
    "subTotal": 175000,
    "discount": 10000,
    "shipping": 15000,
    "totalPrice": 180000
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
  - `/api/v1/delivery/start`

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
    "orderNo": "ORD-12345",
    "driverId": "62f8d408-d483-41f2-8ddc-ea1c11900d41",
    "customer": "John Doe",
    "address": "123 Main Street, Jakarta",
    "totalWeight": 5,
    "totalPrice": 195000,
    "deliveryStatus": "dikirim",
    "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
    "deliveryStartTime": "2025-03-27T11:56:18.190281",
    "checkInTime": null,
    "checkOutTime": null,
    "lastUpdateTime": "2025-03-27T11:56:18.190281"
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
> delivery → checkin → checkout → return


- URL
  - `/api/v1/delivery`

- Method
  - `PUT`

- Header 
  - `Authorization: Bearer <token>`

- Request Body:
  - `orderNo` as `string`, 
  - `deliveryStatus` as string
    > Possible values: "delivery", "checkin", "checkout", "return"

### Success
```json
{
    "status": "success",
    "message": "Status paket 'OB/01-2025/104' berhasil diupdate",
    "data": {
        "orderNo": "OB/01-2025/104",
        "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
        "deliveryStatus": "checkout",
        "customer": "John Doe",
        "address": "123 Main Street, Central Jakarta",
        "totalWeight": 6.7,
        "totalPrice": 576000.0,
        "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
        "deliveryStartTime": "2025-03-30T15:00:54.307042+00:00",
        "checkInTime": "2025-03-31T03:17:59.852427",
        "checkOutTime": "2025-03-31T03:18:31.059068",                
        "returnTime": "2025-03-31T03:18:21.226109",
        "lastUpdateTime": "2025-03-31T03:18:31.059068"
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
        "orderNo": "OB/01-2025/104",
        "driverId": "c2c73f9e-3fff-4e11-afe1-f482bf051302",
        "deliveryStatus": "checkout",
        "customer": "John Doe",
        "address": "123 Main Street, Central Jakarta",
        "totalWeight": 6.7,
        "totalPrice": 576000.0,
        "trackerId": "Ue2KlB6IMPdfoBN4CR2b",
        "deliveryStartTime": "2025-03-30T15:00:54.307042+00:00",
        "checkInTime": "2025-03-31T03:17:59.852427",
        "checkOutTime": "2025-03-31T03:18:31.059068",                
        "returnTime": "2025-03-31T03:18:21.226109",
        "lastUpdateTime": "2025-03-31T03:18:31.059068"
    }
}
```

# User Endpoint
## Dashboard
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
                "deliveryStatus": "dikirim",
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
                "deliveryStatus": "dikembalikan",
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
                "deliveryStatus": "selesai",
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
                "deliveryStatus": "dikirim",
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
                "deliveryStatus": "dikirim",
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
                "deliveryStatus": "sampai",
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
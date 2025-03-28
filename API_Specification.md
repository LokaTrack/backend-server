
# API Specification

This document provides the specifications for the API endpoints of our application. Each endpoint is described with its URL, HTTP method, request parameters, and possible responses. The API is designed to be RESTful and follows standard conventions for request and response formats.

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

#### fail
if fail - wrong email or password (Status code 401)
```json
{
  "status": "fail",
  "message": "Email atau password salah",
  "timestamp": "xxxxxx"
}
```

## 3. User Profile 
- URL
  - `/api/v1/user`

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

## 4. Add Package
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

## 5. Get Package Detail
- URL
  - `/api/v1/package/detail`

- Method
  - `GET`

- Header 
  - `Authorization: Bearer <token>`

- Query Parameters:
  - `orderNo` as `string`

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


## 6. Start Delivery Package
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



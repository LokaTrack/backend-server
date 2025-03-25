
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

#### If Success
Success  (Status code 201) :
```json
{
  "status": "success",
  "message": "Akun anda berhasil dibuat!"
}
```

#### If Fail
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

if fail - password less than 8 character (Status code 400):
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
  - POST
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

## 3. Add Package
- URL
  - `/api/v1/package/add`

- Method
  - `POST`

- Request Body:
  - `packageId` as `string`, must be unique
  - `recipientName` as `string`
  - `recipientNumber` as `integer`
  - `recipientAddress` as `string`
  - `packageWeight` as `float`
  - `packageDimension` as object
      - `length` as float
      - `width` as float
      - `height` as float
  - `additionalNotes` as `string` (optional)


### Success (Status code 201):
```json
{
  "status": "success",
  "message": "Paket berhasil ditambahkan",
  "data": {
    "packageId": "PKG12345",
    "recipientName": "John Doe",
    "recipientNumber": 81234567890,
    "recipientAddress": "Jl. Jend. Sudirman No. 1, Jakarta",
    "packageWeight": 2.5,
    "packageDimension": {
      "length": 10.0,
      "width": 5.0,
      "height": 5.0
    },
    "additionalNotes": "Fragile, Handle with care"
  }
}
```

### Failure
If fail - internal error (Status code 500):
```json
{
  "status": "fail",
  "message": "Terjadi kesalahan: [error details]",
  "timestamp": "2025-03-25T21:30:00.000000"
}
```

## 4. Start Delivery Package
- URL
  - `/api/v1/package/start`

- Method
  - `POST`

- Request Body:
  - `packageId` as `string`, must exist in packageCollection
  - `driverId` as `string`
  - `trackerId` as `string` (optional)
  - `deliveryStatus` as `string` (always set to "in_transit" on creation)
  - `deliveryStartTime` as `datetime`
  - `deliveryStartLocation` as `object`
  - `latitude` as `float`
  - `longitude` as `float`

### Success
Success (Status code 201):
```json
{
  "status": "success",
  "message": "Paket berhasil ditambahkan ke delivery",
  "data": {
    "packageId": "PKG12345",
    "driverId": "DRV98765",
    "trackerId": "TRK54321",
    "deliveryStatus": "in_transit",
    "deliveryStartTime": "2025-03-25T21:30:00.000000",
    "deliveryStartLocation": {
      "latitude": -6.2088,
      "longitude": 106.8456
    },
    "checkInTime": null,
    "checkInLocation": {
      "latitude": 0.0,
      "longitude": 0.0
    },
    "checkOutTime": null,
    "checkOutLocation": {
      "latitude": 0.0,
      "longitude": 0.0
    }
  }
}
```

Failure
If fail - package not found (Status code 404):
```json
{
  "status": "fail",
  "message": "Paket dengan id 'PKG12345' tidak ditemukan.",
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



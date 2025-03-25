
# API Specification

This document provides the specifications for the API endpoints of our application. Each endpoint is described with its URL, HTTP method, request parameters, and possible responses. The API is designed to be RESTful and follows standard conventions for request and response formats.

## 1. Register Process
- URL
  - `/api/v1/register`
- Method
  - POST
- Request Body :
  - `email` as `string`, must be `unique`
  - `username` as string
  - `password` as `string`, must be at least 8 characters
  - `password-confirmation` as `string`, must be same as password

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

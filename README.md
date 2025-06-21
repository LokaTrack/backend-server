<div align="center">

  <img src="https://storage.googleapis.com/lokatrack-bucket/assets/lokatrack_logo_no_bg.png" alt="LokaTrack Logo" width="200" />

  <h1>LokaTrack - Backend API</h1>

  <p>
    The backend server for the LokaTrack application, a comprehensive system for delivery tracking and automated document processing using OCR.
  </p>

  <p>
    <img src="https://img.shields.io/badge/Version-1.0.0-green?style=for-the-badge" alt="Version"/>
    <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"/>
    <img src="https://img.shields.io/badge/Deployment-GCP-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white" alt="Deployment"/>
  </p>

  <p>
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Firestore-FFCA28?style=flat-square&logo=firebase&logoColor=white" alt="Firestore" />
    <img src="https://img.shields.io/badge/EMQX-3DDC84?style=flat-square&logo=mqtt&logoColor=white" alt="EMQX" />
    <img src="https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
  </p>

</div>

---

<details open="open">
  <summary><strong>Table of Contents</strong></summary>
  <ol>
    <li><a href="#key-features">Key Features</a></li>
    <li><a href="#technology-stack">Technology Stack</a></li>
    <li><a href="#project-structure">Project Structure</a></li>
    <li><a href="#api-response-format">API Response Format</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation-and-setup">Installation & Setup</a></li>
      </ul>
    </li>
    <li><a href="#running-with-docker">Running with Docker</a></li>
  </ol>
</details>


# LokaTrack Backend Server
This repository contains the source code for the LokaTrack backend server. Built with **FastAPI**, this high-performance, asynchronous API serves as the core for a comprehensive delivery tracking and OCR-based document processing system.

It is designed to connect with IoT devices, a Flutter mobile application, and a web-based administrative dashboard, providing a complete end-to-end solution for logistics management.

## Key Features
- **RESTful API**: Provides a complete set of endpoints for user authentication, package management, delivery status updates, and administrative functions.
- **Real-Time GPS Tracking**: Ingests encrypted location data from IoT devices via a self-hosted EMQX MQTT broker.
- **Automated Document Processing**: Utilizes PaddleOCR to automatically extract item details from uploaded delivery order images.
- **Secure Authentication**: Implements JWT (JSON Web Tokens) for stateless and secure endpoint protection, with password hashing using Bcrypt.
- **Cloud-Native Integration**: Natively integrated with Google Cloud Platform (GCP), using Firestore for the NoSQL database and Cloud Storage for media files.
- **Real-time Dashboard Updates**: Pushes live data to the web dashboard using Socket.IO.

## Technology Stack
- **Backend**: Python 3.11, FastAPI, Pydantic, Uvicorn
- **Database & Storage**: Google Firestore, Google Cloud Storage
- **Real-time & Messaging**: EMQX (MQTT Broker), Paho-MQTT, Socket.IO
- **Image Processing**: PyVIPS (for compression), PaddleOCR
- **Security**: JWT (python-jose), Bcrypt (passlib), ChaCha20 (pycryptodome)
- **Deployment**: Docker, Nginx, Supervisor, GitHub Actions


## Project Structure
```
backend-server/
├── 📁 app/                          # Main application directory
│   ├── 📄 main.py                   # FastAPI application entry point
│   ├── 📁 config/                   # Configuration files (database, MQTT, storage)
│   ├── 📁 models/                   # Pydantic data models for validation
│   ├── 📁 routers/                  # API route handlers and endpoints
│   ├── 📁 services/                 # Business logic layer
│   ├── 📁 templates/                # HTML email templates
│   └── 📁 utils/                    # Utility functions (compression, helpers)
│── 📄 .env                          # Environment variables configuration
└── 📄 requirements.txt              # Python dependencies
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


# Getting Started
Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

## Prerequisites
- Python 3.10 or higher
- pip and virtualenv
- libvips
```sh
# For Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv
sudo apt-get install -y libvips-dev
```
- Service Account JSON from Google Cloud Platform
  - Create a service account in your GCP project with Firestore and Cloud Storage access.
  - Download the service account key as a JSON file and place it in the root directory of the project.
- Mailgun Account for sending emails

## Installation and Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/LokaTrack/backend-server.git
   cd backend-server
   ```
2. Create and activate a virtual environment::
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure Environment Variables
Create a .env file in the root directory by copying the example below. Fill in the values with your actual service credentials.
   ```.env
   # Google Cloud
   PROJECT_ID=your-gcp-project-id
   GCS_BUCKET_NAME=your-gcs-bucket-name
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service_account.json
   
   # jwt token for security utils
   SECRET_KEY=your_super_secret_key_for_jwt
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRED_DAYS=30
   
   # Mailgun configuration
   MAILGUN_API_KEY=your_mailgun_api_key
   MAILGUN_DOMAIN=your_mailgun_domain
   EMAIL_FROM=no-reply@yourdomain.com
   
   # Application URLs
   APP_DOMAIN=yourdomain.com
   FRONTEND_URL=yourdomain.com
   
   # MQTT Configuration
   MQTT_BROKER=your_mqtt_broker_address
   MQTT_TOPIC=your_mqtt_topic_for_gps
   MQTT_PORT=1883
   MQTT_CLIENT_ID=your_mqtt_client_id_for_server
   MQTT_USERNAME=your_mqtt_username
   MQTT_PASSWORD=your_mqtt_password
   MQTT_TLS= false 
   MQTT_ENCRYPT_KEY=a_32_byte_hex_encoded_key_for_chacha20
   
   # Logging Configuration, Use DEBUG, INFO, WARNING, ERROR, or CRITICAL
   LOG_LEVEL=DEBUG
   
   # NTP Server Configuration
   NTP_SERVER=time.nist.gov
   ```

5. Start the server:
   ```bash
   uvicorn app.main:server --reload
   ```
   The server will be running at http://127.0.0.1:8000.


## API Documentation
You can access the interactive API documentation at:
http://127.0.0.1:8000/api/v1/lokatrack/docs

# Running with Docker 
For a more consistent and isolated environment, you can run the application using Docker. Make sure you have Docker installed on your system.
Note: Please follow the previous steps to create the `.env` and `service_account.json` files.
1. Build the Docker Image
    ```bash
    docker build -t lokatrack-backend .
    ```

2. Run the Docker Container
    ```bash
    docker run -d -p 8000:8000 \
        --name lokatrack-app \
        --env-file .env \
        -e GOOGLE_APPLICATION_CREDENTIALS=/app/service_account.json \
        -v "your-path\service_account.json":/app/service_account.json \
        lokatrack-backend
    ```
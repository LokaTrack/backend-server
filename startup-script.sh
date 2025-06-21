#!/bin/bash
# Startup Script for Lokatrack VM
# This setup automates:
# - FastAPI backend run by Supervisor.
# - React frontend run as a Docker Container.
# - Nginx on the host as a reverse proxy for both.

# Exit immediately if a command fails.
set -e

# --- Configuration Variables (Adjust to your needs) ---
APP_USER="cornelius"
APP_USER_HOME="/home/${APP_USER}"
REPO_URL="https://github.com/LokaTrack/backend-server.git" # REPLACE with your Git Repository URL
APP_DIR="${APP_USER_HOME}/LokaTrack"
BACKEND_DIR="${APP_DIR}/backend-server"
GCP_PROJECT_ID="lokatrack"          

SECRET_NAME_ENV_FILE="backend-secret" # Name of the secret in Secret Manager containing the backend .env
CERT_BUCKET="lokatrack-bucket"           # GCS Bucket name for SSL certificate backup
FRONTEND_IMAGE="corneliusy/lokatrack:latest" # Docker image name for the frontend

# --- 1. System Preparation and Dependencies ---
echo "Starting system preparation and dependency installation..."
apt-get update -y
apt-get install -y \
    nginx \
    supervisor \
    python3-venv \
    python3-pip \
    git \
    libvips-dev \
    tesseract-ocr \
    docker.io \
    libgl1

echo "System dependency installation complete."

# curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
# sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# --- 2. User and Directory Setup ---
if ! id -u ${APP_USER} >/dev/null 2>&1; then
    echo "Creating user: ${APP_USER}..."
    useradd -m -s /bin/bash ${APP_USER}
fi
# Add user to the docker group to run docker commands without sudo
usermod -aG docker ${APP_USER}

echo "Creating application directory at ${APP_DIR}..."
mkdir -p "${APP_DIR}"

# --- 3. Fetch Backend Application Code from Git ---
echo "Fetching backend code from Git repository: ${REPO_URL}..."
rm -rf "${APP_DIR}"
sudo -u ${APP_USER} git clone "${REPO_URL}" "${BACKEND_DIR}"

# --- 4. Setup Backend (Python FastAPI) ---
echo "Setting up FastAPI backend..."
cd "${BACKEND_DIR}"
sudo -u ${APP_USER} python3 -m venv env
sudo -u ${APP_USER} bash -c "source ${BACKEND_DIR}/env/bin/activate && pip install --no-cache-dir -r ${BACKEND_DIR}/requirements.txt"

# install additional dependencies
sudo -u ${APP_USER} bash -c "source ${BACKEND_DIR}/env/bin/activate && pip install --no-cache-dir opencv-contrib-python==4.10.0.84 opencv-python-headless==4.11.0.86"

echo "Fetching .env file from Secret Manager..."
gcloud secrets versions access latest --secret="${SECRET_NAME_ENV_FILE}" --project="${GCP_PROJECT_ID}" > "${BACKEND_DIR}/.env"
chown ${APP_USER}:${APP_USER} "${BACKEND_DIR}/.env"

# --- 5. Setup Supervisor for Backend ---
echo "Creating Supervisor configuration for the backend..."
cat <<EOF > /etc/supervisor/conf.d/lokatrack-backend.conf
[program:lokatrack-backend]
command=${BACKEND_DIR}/env/bin/python -m app.main --host 127.0.0.1 --port 8000 --env-file ${BACKEND_DIR}/.env
directory=${BACKEND_DIR}
user=${APP_USER}
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/lokatrack-backend.err.log
stdout_logfile=/var/log/supervisor/lokatrack-backend.out.log
EOF

# # --- 7. Setup Google Cloud Ops Agent ---
# echo "Creating configuration for Google Cloud Ops Agent..."
# cat <<EOF > /etc/google-cloud-ops-agent/config.yaml
# logging:
#   receivers:
#     lokatrack_stdout:
#       type: files
#       include_paths:
#         - /var/log/lokatrack_log/lokatrack.out.log
#     lokatrack_stderr:
#       type: files
#       include_paths:
#         - /var/log/lokatrack_log/lokatrack.err.log
#   service:
#     pipelines:
#       lokatrack_pipeline:
#         receivers: [lokatrack_stdout, lokatrack_stderr]
# EOF

# --- 6. Setup Frontend (from Docker Registry) ---
echo "Setting up frontend from Docker Registry: ${FRONTEND_IMAGE}..."
# Login to Docker Hub if your image is private (if public, this is not necessary)
# You can store credentials as a secret and retrieve them here
DOCKER_HUB_PASSWORD=$(gcloud secrets versions access latest --secret="docker_token" --project="${GCP_PROJECT_ID}")
echo "${DOCKER_HUB_PASSWORD}" | docker login --username corneliusy --password-stdin

# Pull the latest image
docker pull "${FRONTEND_IMAGE}"

# Stop and remove the old container if it exists to ensure an update
if [ $(docker ps -a -q -f name=lokatrack-web) ]; then
    docker stop lokatrack-web
    docker rm lokatrack-web
fi

# Run the frontend container
docker run -d \
  -p 127.0.0.1:8080:80 \
  --name lokatrack-web \
  --restart always \
  "${FRONTEND_IMAGE}"

# --- 7. Setup Nginx as a Reverse Proxy ---
echo "Creating Nginx configuration..."
# Fetching SSL certificates from GCS
echo "Fetching SSL certificates from GCS Bucket: gs://${CERT_BUCKET}/..."
mkdir -p /etc/letsencrypt
gsutil -m cp -r "gs://${CERT_BUCKET}/letsencrypt/*" /etc/letsencrypt/

# Creating Nginx configuration file
cat <<'EOF' > /etc/nginx/sites-available/lokatrack
server {
    server_name lokatrack.me; # Uncommented and set properly

#    location / {
#        root /var/www/html;
#        index lokatrack-under-development.html;
#        # If file not found, return forbidden
#        try_files $uri $uri/ =403;
#    }

    location / {
        # Point to your frontend server
        proxy_pass http://127.0.0.1:8080; 
#       root /var/www/html;
#       index lokatrack-under-development.html;
#       limit_req zone=req_limit burst=10 nodelay;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Additional settings for SPA (Single Page Application) like React
        # to ensure page refresh and direct URL access work correctly
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade"; # Important for hot-reloading React dev server if present
    }

    location /.well-known/ {
        root /var/www/html;
        allow all;
    }

    # Root location for the application
    location /api/v1 {
        proxy_pass http://127.0.0.1:8000;
#       limit_req zone=req_limit burst=5 nodelay;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 20M;

        # Connection timeout
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    location /verify-email {
        proxy_pass http://127.0.0.1:8000/verify-email;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Connection timeout
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:8000/socket.io;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    
        # WebSocket connections can be long-lived
        proxy_read_timeout 86400;
        proxy_connect_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Log for debugging
    access_log /var/log/nginx/lokatrack_access.log;
    error_log /var/log/nginx/lokatrack_error.log;

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/lokatrack.me/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/lokatrack.me/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name lokatrack.me;

    # Redirect any HTTP request to HTTPS
    return 301 https://$host$request_uri;
}

# Default server block for unmatched requests on port 80
server {
    listen 80 default_server;
    server_name _;

    return 444;
}

# Default server block for unmatched requests on port 443
server {
    listen 443 default_server ssl;
    listen [::]:443 default_server ssl;
    server_name _;

    ssl_certificate /etc/letsencrypt/live/lokatrack.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lokatrack.me/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 444;
}
EOF

# Activating Nginx site
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi
ln -sf /etc/nginx/sites-available/lokatrack /etc/nginx/sites-enabled/lokatrack

# --- 8. Start and Enable Services ---
echo "Starting all services..."
supervisorctl reread
supervisorctl update
supervisorctl start lokatrack-backend

# Restart Nginx to apply the new configuration
systemctl restart nginx

# Enable services to run on boot
systemctl enable supervisor
systemctl enable nginx
systemctl enable docker

# Restart Ops Agent to apply new logging configuration
# systemctl restart google-cloud-ops-agent

echo "Startup script finished. The Lokatrack application is now running."
# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variable to prevent Python output from being buffered
ENV PYTHONUNBUFFERED 1

# Install system dependencies needed
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libvips-dev \
    libgl1-mesa-glx \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code from the 'app' directory to the '/app' working directory in the container
COPY ./app ./app

# The ports that will be exposed by your application
EXPOSE 8000
EXPOSE 1883
EXPOSE 8883

# Command to run the application using Uvicorn
# NOTE: The .env and service_account.json files will be mounted at runtime, not built into the image.
CMD ["uvicorn", "app.main:server", "--host", "0.0.0.0", "--port", "8000"]
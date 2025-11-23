# Use an official Python runtime as a parent image
# python:3.9-slim (or 3.10/3.11) is good, but -slim images lack some system tools
# so we must install them manually.
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# 1. Install System Dependencies
# We need:
# - potrace: for tracing
# - imagemagick: for converting images to BMP (required by potrace)
# - build-essential: often needed for installing some python packages
RUN apt-get update && apt-get install -y \
    potrace \
    imagemagick \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy (it often blocks PDF/script usage by default, 
# strictly optional for simple images but good practice if you expand later)
# For basic PNG->BMP, the default policy is usually fine.

# 2. Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy Application Code
COPY . .

# Expose the port
EXPOSE 5001

# Run the server
CMD ["python", "src/server.py"]
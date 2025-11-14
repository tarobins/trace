# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y pkg-config libagg-dev build-essential libpotrace-dev openssl
RUN pip install --no-cache-dir -r requirements.txt

# Generate self-signed certificate
RUN openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes -subj "/C=XX/ST=StateName/L=CityName/O=CompanyName/OU=OrgName/CN=localhost"

# Copy the rest of the application's code
COPY src/ ./src/

# Create the uploads and processed directories
RUN mkdir -p /app/uploads && mkdir -p /app/processed

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Run the application
CMD ["python", "src/server.py"]

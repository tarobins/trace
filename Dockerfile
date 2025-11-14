# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y pkg-config libagg-dev build-essential libpotrace-dev
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY src/ ./src/
COPY cert.pem .
COPY key.pem .

# Create the uploads and processed directories
RUN mkdir -p /app/uploads && mkdir -p /app/processed

# Make port 5001 available to the world outside this container
EXPOSE 5001

# Run the application
CMD ["python", "src/server.py"]

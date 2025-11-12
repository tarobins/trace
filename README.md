# Image Tracer

This project provides a web service to trace JPG or PNG images into SVG format.

## Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate SSL Certificates:**
    The server runs with SSL. You need to generate self-signed certificates.
    ```bash
    openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
    ```
    When prompted, you can enter arbitrary information, or just hit enter to accept defaults for most fields. The "Common Name" can be `localhost`.

## Running the Server

1.  **Activate your virtual environment (if not already active):**
    ```bash
    source .venv/bin/activate
    ```

2.  **Start the Flask server:**
    ```bash
    python src/server.py
    ```

The server will be accessible at `https://localhost:5001`.
import os
import subprocess
import tempfile

def trace_image_from_path(image_path):
    """
    Takes a file path, traces it, and returns the SVG string.
    """
    print(f"--- [DEBUG] Starting trace from path: {image_path} ---")
    if not os.path.exists(image_path):
        print(f"!!! [ERROR] File not found at path: {image_path}")
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Create a temp file for the BMP (potrace needs BMP)
    with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as bmp_file:
        bmp_path = bmp_file.name
    
    print(f"--- [DEBUG] Intermediate BMP path: {bmp_path} ---")

    try:
        # Convert image to BMP using ImageMagick (convert)
        # -monochrome forces black and white for better tracing
        print("--- [DEBUG] Running 'convert' command... ---")
        subprocess.check_call(['convert', image_path, '-monochrome', bmp_path])

        if not os.path.exists(bmp_path) or os.path.getsize(bmp_path) == 0:
             print("!!! [ERROR] 'convert' command failed to create a valid BMP file.")
             raise Exception("Image conversion failed.")
        print(f"--- [DEBUG] BMP created successfully. Size: {os.path.getsize(bmp_path)} bytes ---")

        # Run potrace to create SVG
        # -s: SVG output
        # -k 0.8: Black/white cutoff (tuning this helps with stickers)
        print("--- [DEBUG] Running 'potrace' command... ---")
        proc = subprocess.Popen(['potrace', '-s', '-k', '0.8', bmp_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        svg_content_bytes, stderr = proc.communicate()
        
        if proc.returncode != 0:
            print(f"!!! [ERROR] 'potrace' failed. Error: {stderr.decode('utf-8')}")
            raise Exception(f"Potrace failed: {stderr.decode('utf-8')}")
            
        svg_content = svg_content_bytes.decode('utf-8')
        print(f"--- [DEBUG] Trace successful. SVG content length: {len(svg_content)} ---")
        
        return svg_content

    finally:
        if os.path.exists(bmp_path):
            os.remove(bmp_path)
            print(f"--- [DEBUG] Cleaned up BMP file: {bmp_path} ---")

def trace_image_bytes(image_data):
    """
    Takes raw image bytes, saves to temp, traces, and cleans up.
    """
    print(f"--- [DEBUG] Starting trace from bytes. Data length: {len(image_data)} bytes ---")
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
        temp_img.write(image_data)
        temp_img_path = temp_img.name
    
    print(f"--- [DEBUG] Saved bytes to temporary file: {temp_img_path} ---")
    
    try:
        return trace_image_from_path(temp_img_path)
    finally:
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
            print(f"--- [DEBUG] Cleaned up temporary image file: {temp_img_path} ---")
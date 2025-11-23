import os
import subprocess
import tempfile

def trace_image_from_path(image_path):
    """
    Takes a file path, traces it, and returns the SVG string.
    """
    # Create a temp file for the BMP (potrace needs BMP)
    with tempfile.NamedTemporaryFile(suffix='.bmp', delete=False) as bmp_file:
        bmp_path = bmp_file.name

    try:
        # 1. Convert image to BMP using ImageMagick
        # -monochrome forces black and white for better tracing
        subprocess.check_call(['convert', image_path, '-monochrome', bmp_path])

        # 2. Run potrace to create SVG
        # -s: SVG output
        # -k 0.8: Black/white cutoff (tuning this helps with stickers)
        # -o -: FORCE output to stdout (Critical Fix!)
        proc = subprocess.Popen(
            ['potrace', '-s', '-k', '0.8', bmp_path, '-o', '-'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        svg_content_bytes, stderr = proc.communicate()
        
        if proc.returncode != 0:
            raise Exception(f"Potrace failed: {stderr.decode('utf-8')}")
            
        svg_content = svg_content_bytes.decode('utf-8')
        
        if not svg_content.strip():
            raise Exception("Tracing produced empty output")

        return svg_content

    finally:
        if os.path.exists(bmp_path):
            os.remove(bmp_path)

def trace_image_bytes(image_data):
    """
    Takes raw image bytes, saves to temp, traces, and cleans up.
    """
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
        temp_img.write(image_data)
        temp_img_path = temp_img.name
    
    try:
        return trace_image_from_path(temp_img_path)
    finally:
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
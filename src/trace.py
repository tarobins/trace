import sys
import os
from PIL import Image
import numpy as np
from potrace import Bitmap

def trace(filename):
    """
    Traces a bitmap image to an SVG vector graphic using settings
    that mimic Inkscape's default "Trace Bitmap" functionality.
    """
    # Open the image and convert it to a bitmap
    img = Image.open(filename)
    
    # Convert to grayscale
    img = img.convert("L")

    # Convert to numpy array and apply threshold
    data = np.array(img)
    threshold = 0.45 * 255
    data[data > threshold] = 255
    data[data <= threshold] = 0

    # Create a potrace.Bitmap object from the numpy array
    bitmap = Bitmap(data)

    # Trace the bitmap with parameters to mimic Inkscape's defaults
    # turdsize: Suppress speckles of up to this size (default 2). 
    #   Inkscape's "Speckles" setting is disabled by default, so we set this to 0.
    # opttolerance: Curve optimization tolerance (default 0.2).
    #   Inkscape's "Optimize" setting defaults to 0.2.
    # alphamax: Corner threshold parameter (default 1.0).
    #   Inkscape's "Smooth corners" defaults to 1.0.
    path_list = bitmap.trace(turdsize=2, opttolerance=0.4, alphamax=1.0)

    # Get the SVG output
    width, height = img.size
    path_data = []
    for curve in path_list:
        path_data.append(f'M{curve.start_point.x},{curve.start_point.y}')
        for segment in curve:
            if segment.is_corner:
                path_data.append(f'L{segment.c.x},{segment.c.y}L{segment.end_point.x},{segment.end_point.y}')
            else:
                path_data.append(f'C{segment.c1.x},{segment.c1.y} {segment.c2.x},{segment.c2.y} {segment.end_point.x},{segment.end_point.y}')
        path_data.append('Z')
    
    path_d = "".join(path_data)

    svg_data = [f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">']
    svg_data.append(f'<path d="{path_d}" fill="black" stroke="none"/>')
    svg_data.append('</svg>')
    
    svg = "".join(svg_data)

    # Save the SVG to a file
    basename, _ = os.path.splitext(filename)
    svg_filename = basename + ".svg"
    with open(svg_filename, "w") as f:
        f.write(svg)

    print(f"Successfully traced {filename} to {svg_filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python trace.py <filename.jpg>")
        sys.exit(1)
    
    filename = sys.argv[1]
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    trace(filename)

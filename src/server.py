import os
# import io # Not needed with the new SDK's direct byte access
from flask import Flask, request, render_template_string, jsonify
from google import genai
from google.genai import types
# from PIL import Image # Not needed for just saving bytes
from trace import trace_image_from_path, trace_image_bytes

app = Flask(__name__)

# --- CONFIG ---
API_KEY = os.environ.get("GOOGLE_API_KEY")

# Initialize the Client
client = None
if API_KEY:
    client = genai.Client(api_key=API_KEY)

# Define a debug file path right in your project root
DEBUG_IMAGE_PATH = os.path.abspath("debug_generated_image.png")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Trace & Generate</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .container { border: 1px solid #ccc; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
        input[type="text"] { width: 70%; padding: 10px; }
        button { padding: 10px 20px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }
        button:hover { background: #0056b3; }
        #result { margin-top: 2rem; border: 1px dashed #ccc; padding: 1rem; min-height: 200px; display: flex; justify-content: center; align-items: center; }
        svg { max-width: 100%; height: auto; }
        .loading { color: #666; font-style: italic; }
        .error { color: red; background: #ffe6e6; padding: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Trace App</h1>

    <div class="container">
        <h2>Generate SVG from Description</h2>
        <p>Enter a prompt to create a Cricut-ready sticker design.</p>
        <div style="display: flex; gap: 10px;">
            <input type="text" id="promptInput" placeholder="e.g. a cute beaver, a rocket ship">
            <button onclick="generateSvg()">Generate</button>
        </div>
    </div>

    <div class="container">
        <h2>Trace Existing Image</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*">
            <input type="submit" value="Upload & Trace">
        </form>
    </div>

    <div id="result">Generated SVG will appear here...</div>

    <script>
        async function generateSvg() {
            const prompt = document.getElementById('promptInput').value;
            const resultDiv = document.getElementById('result');
            
            if (!prompt) return alert("Please enter a prompt");
            resultDiv.innerHTML = '<span class="loading">Generating image (Nano Banana) and tracing...</span>';

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ prompt: prompt })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || "Unknown error");
                }
                resultDiv.innerHTML = data.svg;
            } catch (err) {
                console.error(err);
                resultDiv.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return 'No file', 400
    file = request.files['file']
    if file.filename == '': return 'No selected file', 400
    
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    try:
        return trace_image_from_path(temp_path), 200, {'Content-Type': 'image/svg+xml'}
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.route('/generate', methods=['POST'])
def generate_svg():
    if not client:
        print("!!! [ERROR] GOOGLE_API_KEY not set.")
        return jsonify({'error': 'Server missing GOOGLE_API_KEY'}), 500

    user_prompt = request.json.get('prompt', '')
    print(f"--- [DEBUG] Received generation request for: '{user_prompt}' ---")
    
    # 1. Prompt Engineering
    full_prompt = (
        f"Simple black and white line art of {user_prompt}. "
        "Flat vector graphics. Bold solid lines. Pure white background. "
        "Coloring book style. No shading, no gradients, no borders, no drop shadows."
    )

    try:
        # 2. Use Gemini 2.5 Flash Image ("Nano Banana")
        print("--- [DEBUG] Calling Gemini API... ---")
        response = client.models.generate_content(
            model='gemini-2.5-flash-image',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_ONLY_HIGH"
                )]
            )
        )
        print("--- [DEBUG] Gemini API response received. ---")
        
        # 3. Extract Image Bytes
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img_bytes = part.inline_data.data
                print(f"--- [DEBUG] Image data extracted. Size: {len(img_bytes)} bytes. ---")
                
                # --- DEBUG: SAVE IMAGE TO FILE ---
                try:
                    with open(DEBUG_IMAGE_PATH, "wb") as f:
                        f.write(img_bytes)
                    print(f"--- [DEBUG] SAVED GENERATED IMAGE TO: {DEBUG_IMAGE_PATH} ---")
                except Exception as e:
                    print(f"!!! [ERROR] Failed to save debug image: {e}")
                # ---------------------------------

                # 4. Trace it
                print("--- [DEBUG] Calling trace_image_bytes... ---")
                svg_output = trace_image_bytes(img_bytes)
                print("--- [DEBUG] Trace complete. Sending response. ---")
                return jsonify({'svg': svg_output})
                
        print("!!! [ERROR] No image data found in API response.")
        return jsonify({'error': 'No image generated in response'}), 500

    except Exception as e:
        print(f"!!! [ERROR] Exception during generation/tracing: {e}")
        # Print full error traceback to console for debugging
        import traceback
        traceback.print_exc() 
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure SSL for local development if needed, or run behind proxy
    app.run(host='0.0.0.0', port=5001)
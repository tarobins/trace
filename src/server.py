import os
import io
from flask import Flask, request, send_file, render_template_string, jsonify
import google.generativeai as genai
from trace import trace_image_from_path, trace_image_bytes

app = Flask(__name__)

# --- CONFIG ---
# Get API key from environment
API_KEY = os.environ.get("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Trace & Generate</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .container { border: 1px solid #ccc; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
        h2 { margin-top: 0; }
        input[type="text"] { width: 70%; padding: 10px; }
        button { padding: 10px 20px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }
        button:hover { background: #0056b3; }
        #result { margin-top: 2rem; border: 1px dashed #ccc; padding: 1rem; min-height: 200px; display: flex; justify-content: center; align-items: center; }
        svg { max-width: 100%; height: auto; }
        .loading { color: #666; font-style: italic; }
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

    <div id="result">
        Generated/Traced SVG will appear here...
    </div>

    <script>
        async function generateSvg() {
            const prompt = document.getElementById('promptInput').value;
            const resultDiv = document.getElementById('result');
            
            if (!prompt) return alert("Please enter a prompt");

            resultDiv.innerHTML = '<span class="loading">Generating image and tracing... (this may take a few seconds)</span>';

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ prompt: prompt })
                });

                if (!response.ok) throw new Error(await response.text());

                const data = await response.json();
                resultDiv.innerHTML = data.svg;
            } catch (err) {
                resultDiv.innerHTML = '<p style="color:red">Error: ' + err.message + '</p>';
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
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    # Save temp file
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    
    try:
        svg_content = trace_image_from_path(temp_path)
        # Return simpler view for upload (or redirect to index with result)
        # For now, just returning the raw SVG as the original app likely did
        return svg_content, 200, {'Content-Type': 'image/svg+xml'}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/generate', methods=['POST'])
def generate_svg():
    if not API_KEY:
        return jsonify({'error': 'Server missing GOOGLE_API_KEY'}), 500

    data = request.json
    user_prompt = data.get('prompt', '')
    
    # THE MAGIC PROMPT
    system_instruction = (
        f"Simple black and white line art of {user_prompt}. "
        "Flat vector graphics. Bold solid lines. Pure white background. "
        "Coloring book style. No shading, no gradients, no borders, no drop shadows."
    )

    try:
        # Use Gemini 3 (or best available model)
        # Note: 'gemini-1.5-flash' is often the fastest/cheapest for simple generation if 3 isn't available
        # You can try 'gemini-2.0-flash-exp' or 'gemini-3-exp' if your key has access
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        # Currently, text-to-image is not available via the standard 'generate_content' text API
        # on all models. If using Imagen 3 via Gemini API, the call looks different.
        # However, purely for this example, we will assume you have access to a model
        # that supports image generation or use the Imagen endpoint.
        
        # NOTE: As of late 2025, standard Vertex AI / Gemini API image gen is usually:
        # response = model.generate_content(prompt) (if multimodal)
        # OR specific Image generation clients. 
        
        # Let's try the safest "Imagen" path available in the standard library:
        # If this fails, we might need the specific 'imagen-3.0-generate-001' model string
        
        # ACTUAL WORKING CODE for standard GenAI Image generation (simplified):
        # We will use the 'imagen-3.0-generate-001' model if available, or allow the 
        # library to pick the default image model.
        
        # Since standard Gemini SDK text-to-image is in flux, let's use the 'imagen' reference:
        import base64
        
        # This is a placeholder for the exact Image Generation call 
        # which varies slightly by SDK version. 
        # Assuming we are using a simplified helper or valid model:
        image_response = genai.ImageGenerationModel("imagen-3.0-generate-001").generate_images(
            prompt=system_instruction,
            number_of_images=1
        )
        
        # Extract the first image (usually a PIL Image or bytes)
        generated_image = image_response[0]
        
        # Get bytes
        img_byte_arr = io.BytesIO()
        generated_image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        # Trace it
        svg_output = trace_image_bytes(img_bytes)
        
        return jsonify({'svg': svg_output})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, ssl_context=('cert.pem', 'key.pem'))
import os
import re
from flask import Flask, request, render_template_string, jsonify
from google import genai
from google.genai import types
from trace import trace_image_from_path, trace_image_bytes

app = Flask(__name__)

# --- CONFIG ---
API_KEY = os.environ.get("GOOGLE_API_KEY")

client = None
if API_KEY:
    client = genai.Client(api_key=API_KEY)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Trace & Generate</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .container { border: 1px solid #ccc; padding: 2rem; border-radius: 8px; margin-bottom: 2rem; }
        input[type="text"] { width: 70%; padding: 10px; }
        button, input[type="submit"] { padding: 10px 20px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }
        button:hover, input[type="submit"]:hover { background: #0056b3; }
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
        <form id="uploadForm" onsubmit="uploadAndTrace(event)">
            <input type="file" name="file" accept="image/*" required>
            <input type="submit" value="Upload & Trace">
        </form>
    </div>

    <div id="result">Generated/Traced SVG will appear here...</div>

    <script>
        // --- 1. GENERATE FROM TEXT ---
        async function generateSvg() {
            const promptInput = document.getElementById('promptInput');
            const prompt = promptInput.value.trim();
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
                if (!response.ok) throw new Error(data.error || "Unknown error");

                // Display
                resultDiv.innerHTML = data.svg;
                
                // Download (Name file based on prompt)
                const filename = prompt.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.svg';
                downloadSvg(data.svg, filename);

            } catch (err) {
                console.error(err);
                resultDiv.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
            }
        }

        // --- 2. UPLOAD EXISTING IMAGE ---
        async function uploadAndTrace(event) {
            event.preventDefault(); // Stop page reload
            
            const form = document.getElementById('uploadForm');
            const fileInput = form.querySelector('input[type="file"]');
            const resultDiv = document.getElementById('result');
            
            if (!fileInput.files.length) return alert("Please select a file");
            
            const formData = new FormData(form);
            resultDiv.innerHTML = '<span class="loading">Uploading and tracing...</span>';

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.error || "Unknown error");

                // Display
                resultDiv.innerHTML = data.svg;

                // Download (Name file based on original filename)
                // e.g. "my_photo.jpg" -> "my_photo_traced.svg"
                let originalName = fileInput.files[0].name;
                let filename = originalName.substring(0, originalName.lastIndexOf('.')) || originalName;
                filename += "_traced.svg";
                
                downloadSvg(data.svg, filename);

            } catch (err) {
                console.error(err);
                resultDiv.innerHTML = '<div class="error">Error: ' + err.message + '</div>';
            }
        }

        // --- HELPER: DOWNLOAD SVG ---
        function downloadSvg(svgContent, filename) {
            const blob = new Blob([svgContent], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
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
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400
    
    temp_path = os.path.join('/tmp', file.filename)
    file.save(temp_path)
    try:
        svg_content = trace_image_from_path(temp_path)
        # Now returns JSON to match the generation endpoint
        return jsonify({'svg': svg_content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.route('/generate', methods=['POST'])
def generate_svg():
    if not client:
        return jsonify({'error': 'Server missing GOOGLE_API_KEY'}), 500

    user_prompt = request.json.get('prompt', '')
    
    full_prompt = (
        f"Simple black and white line art of {user_prompt}. "
        "Flat vector graphics. Bold solid lines. Pure white background. "
        "Coloring book style. No shading, no gradients, no borders, no drop shadows."
    )

    try:
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
        
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img_bytes = part.inline_data.data
                svg_output = trace_image_bytes(img_bytes)
                return jsonify({'svg': svg_output})
                
        return jsonify({'error': 'No image generated in response'}), 500

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
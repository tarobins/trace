import os
import zipfile
import time
from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
from trace import trace as trace_image

UPLOAD_FOLDER = os.path.abspath('uploads')
PROCESSED_FOLDER = os.path.abspath('processed')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            return redirect(request.url)

        svg_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(input_path)

                svg_filepath = trace_image(input_path, app.config['PROCESSED_FOLDER'])
                svg_files.append(svg_filepath)

        if len(svg_files) == 1:
            return redirect(url_for('download_file', filename=os.path.basename(svg_files[0])))
        elif len(svg_files) > 1:
            zip_filename = f"traced_images_{int(time.time())}.zip"
            zip_filepath = os.path.join(app.config['PROCESSED_FOLDER'], zip_filename)
            with zipfile.ZipFile(zip_filepath, 'w') as zipf:
                for svg_file in svg_files:
                    zipf.write(svg_file, os.path.basename(svg_file))
            
            return redirect(url_for('download_file', filename=zip_filename))

    return render_template_string('''
    <!doctype html>
    <title>Upload JPG or PNG to Trace</title>
    <h1>Upload a JPG or PNG to trace into an SVG</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file multiple>
      <input type=submit value=Upload>
    </form>
    ''')

@app.route('/processed/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001, ssl_context=('cert.pem', 'key.pem'))

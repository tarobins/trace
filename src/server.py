import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template_string
from werkzeug.utils import secure_filename
from trace import trace as trace_image

UPLOAD_FOLDER = os.path.abspath('uploads')
PROCESSED_FOLDER = os.path.abspath('processed')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}

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
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)

            svg_filepath = trace_image(input_path, app.config['PROCESSED_FOLDER'])
            svg_filename = os.path.basename(svg_filepath)

            return redirect(url_for('download_file', filename=svg_filename))

    return render_template_string('''
    <!doctype html>
    <title>Upload JPG to Trace</title>
    <h1>Upload a JPG to trace into an SVG</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    ''')

@app.route('/processed/<filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

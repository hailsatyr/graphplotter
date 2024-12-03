# Graphplotter service consists of two parts:
#   app.py is the Flask front end web interface
#   plotlyanalyzer.py is the backend script that parses the logs and builds plotly graphs in html format
#       that is displayed by the front end

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from werkzeug.utils import secure_filename
from plotlyanalyzer import process_text_file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PLOT_FOLDER'] = 'plots'

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PLOT_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        
        if file.filename == '':
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

           # Process the file and get the HTML plot
            plot_html = process_text_file(filename)
            return render_template('index.html', plot_html=plot_html)
    
    return render_template('index.html', plot_html=None)

@app.route('/plots/<filename>')
def serve_plot(filename):
    return send_from_directory(app.config['PLOT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

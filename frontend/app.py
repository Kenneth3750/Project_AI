from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder='dist', static_url_path='/')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'message': 'Hello from Flask!',
        'version': '1.0'
    })

@app.route('/resize', methods=['POST'])
def resize_image():
    if 'photo' not in request.files:
        return jsonify({
            'error': 'No file provided'
        }), 400
        
    return jsonify({
        'message': 'Test response from /resize endpoint',
        'received_file': True
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 
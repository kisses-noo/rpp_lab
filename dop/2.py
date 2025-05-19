from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SERVICE2_URL = "http://localhost:5001/count_abc"
SERVICE3_URL = "http://localhost:5002/count_chars"

@app.route('/process_string', methods=['POST'])
def process_string():
    data = request.json
    input_string = data.get('string', '')
    
    try:
        # Запрос к Сервису 2
        abc_response = requests.post(SERVICE2_URL, json={'string': input_string})
        abc_count = abc_response.json().get('count', 0) if abc_response.status_code == 200 else 0
        
        # Запрос к Сервису 3
        chars_response = requests.post(SERVICE3_URL, json={'string': input_string})
        char_count = chars_response.json().get('count', 0) if chars_response.status_code == 200 else 0
        
        return jsonify({
            'abc_count': abc_count,
            'char_count': char_count,
            'status': 'success'
        })
    
    except requests.exceptions.RequestException:
        return jsonify({
            'error': 'Service unavailable',
            'status': 'error'
        }), 503

if __name__ == '__main__':
    app.run(port=5000)
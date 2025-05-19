from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/count_chars', methods=['POST'])
def count_chars():
    data = request.json
    input_string = data.get('string', '')
    count = len(input_string)
    return jsonify({'count': count, 'status': 'success'})

if __name__ == '__main__':
    app.run(port=5002)
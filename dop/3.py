from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/count_abc', methods=['POST'])
def count_abc():
    data = request.json
    input_string = data.get('string', '')
    count = input_string.count('abc')
    return jsonify({'count': count, 'status': 'success'})

if __name__ == '__main__':
    app.run(port=5001)
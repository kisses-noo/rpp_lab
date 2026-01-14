from flask import Flask, request, jsonify

app = Flask(__name__)

# Статические курсы валют
CURRENCY_RATES = {
    "USD": 75.50,
    "EUR": 80.20
}

@app.route('/rate', methods=['GET'])
def get_rate():
    currency = request.args.get('currency', '').upper()
    
    if currency not in CURRENCY_RATES:
        return jsonify({"message": "UNKNOWN CURRENCY"}), 400
    
    try:
        return jsonify({"rate": CURRENCY_RATES[currency]}), 200
    except Exception:
        return jsonify({"message": "UNEXPECTED ERROR"}), 500

if __name__ == '__main__':
    app.run(port=5003)
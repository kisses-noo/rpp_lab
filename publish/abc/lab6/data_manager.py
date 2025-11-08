import os
import psycopg2
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Конфигурация базы данных
db_host = os.getenv('DB_HOST', 'localhost')
db_name = os.getenv('DB_NAME', 'currency_bot')
db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD', 'postgres')

def get_db_connection():
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password
    )

# Маршрут для конвертации валюты
@app.route('/convert', methods=['GET'])
def convert_currency():
    currency_name = request.args.get('currency_name').upper()
    amount = float(request.args.get('amount'))

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency_name,))
        result = cur.fetchone()
        
        if result is None:
            return jsonify({"error": "Валюта не найдена"}), 404
        
        rate = float(result[0])
        converted_amount = amount * rate

        return jsonify({"converted_amount": converted_amount, "rate": float(rate)}), 200
    finally:
        conn.close()

# Маршрут для получения списка всех валют
@app.route('/currencies', methods=['GET'])
def get_currencies():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT currency_name, rate FROM currencies")
        currencies = cur.fetchall()
        
        return jsonify(currencies), 200
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(port=5002)

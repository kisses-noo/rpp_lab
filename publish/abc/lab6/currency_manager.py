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

# Маршрут для добавления валюты 
@app.route('/load', methods=['POST'])
def load_currency():
    data = request.json
    currency_name = data['currency_name'].upper()
    rate = data['rate']

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
        if cur.fetchone():
            return jsonify({"error": "Данная валюта уже существует"}), 400
        
        cur.execute("INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)", (currency_name, rate))
        conn.commit()

        return jsonify({"message": "Валюта успешно добавлена"}), 200
    finally:
        conn.close()

# Маршрут для обновления курса валюты
@app.route('/update_currency', methods=['POST'])
def update_currency():
    data = request.json
    currency_name = data['currency_name'].upper()
    new_rate = data['new_rate']

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
        if not cur.fetchone():
            return jsonify({"error": "Валюта не найдена"}), 404
        
        cur.execute("UPDATE currencies SET rate = %s WHERE currency_name = %s", (new_rate, currency_name))
        conn.commit()

        return jsonify({"message": "Курс успешно обновлен"}), 200
    finally:
        conn.close()

# Маршрут для удаления валюты
@app.route('/delete', methods=['POST'])
def delete_currency():
    data = request.json
    currency_name = data['currency_name'].upper()

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
        if not cur.fetchone():
            return jsonify({"error": "Валюта не найдена"}), 404
        
        cur.execute("DELETE FROM currencies WHERE currency_name = %s", (currency_name,))
        conn.commit()

        return jsonify({"message": "Валюта успешно удалена"}), 200
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(port=5001)

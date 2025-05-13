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

# Маршрут для проверки, является ли пользователь администратором
@app.route('/is_admin/<chat_id>', methods=['GET'])
def is_admin(chat_id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM admins WHERE chat_id = %s", (chat_id,))
        is_admin = cur.fetchone() is not None
        return jsonify({"is_admin": is_admin}), 200
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(port=5003)

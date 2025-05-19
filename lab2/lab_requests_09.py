from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Список возможных операций
operations = ['sum', 'sub', 'mul', 'div']

@app.route('/number/', methods=['GET'])
def get_number():
    # Получаем параметр из запроса
    param = request.args.get('param')
    
    # Проверяем, что параметр есть и это число
    if not param:
        return jsonify({'error': 'The parametr was not entered'}), 400
    
    try:
        param = float(param)
    except ValueError:
        return jsonify({'error': 'The entered parameter is not a number'}), 400
    
    # Генерируем случайное число и умножаем на параметр
    random_num = random.uniform(1, 10)
    result = random_num * param
    
    # Возвращаем результат в JSON формате
    return jsonify({
        'number': result
    })

@app.route('/number/', methods=['POST'])
def post_number():
        
    # Проверяем Content-Type
    if request.headers.get('Content-Type') != 'application/json':
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    # Получаем JSON из тела запроса
    data = request.get_json()
    
    if not data or 'jsonParam' not in data:
        return jsonify({'error': 'The jsonParam parameter is missesng'}), 400
    
    try:
        json_param = float(data['jsonParam'])
    except (ValueError, TypeError):
        return jsonify({'error': 'jsonParam must be a number'}), 400
    
    # Генерируем случайное число и умножаем на параметр
    random_num = random.uniform(1, 10)
    result = random_num * json_param
    
    # Выбираем случайную операцию
    operation = random.choice(operations)
    
    # Возвращаем результат в JSON формате
    return jsonify({
        'number': result,
        'operation': operation
    })

@app.route('/number/', methods=['DELETE'])
def delete_number():
    # Генерируем случайное число
    random_num = random.uniform(1, 10)
    
    # Выбираем случайную операцию
    operation = random.choice(operations)
    
    # Возвращаем результат в JSON формате
    return jsonify({
        'number': random_num,
        'operation': operation
    })
    
if __name__ == '__main__':
    app.run(debug=True)
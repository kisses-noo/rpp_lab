import requests
import random

# 1. GET запрос с параметром param
param = random.uniform(1, 10)
get_response = requests.get(f'http://localhost:5000/number/?param={param}')
get_data = get_response.json()
print(f"GET response: {get_data}")

# 2. POST запрос с JSON телом
json_param = random.uniform(1, 10)
post_response = requests.post(
    'http://localhost:5000/number/',
    json={'jsonParam': json_param},
    headers={'Content-Type': 'application/json'}
)
post_data = post_response.json()
print(f"POST response: {post_data}")

# 3. DELETE запрос
delete_response = requests.delete('http://localhost:5000/number/')
delete_data = delete_response.json()
print(f"DELETE response: {delete_data}")

# 4. Составляем выражение и вычисляем результат
# Получаем все числа и операции
numbers = [get_data['number'], post_data['number'], delete_data['number']]
operations = [post_data['operation'], delete_data['operation']]

# Вычисляем результат последовательно
result = numbers[0]
for i in range(1, len(numbers)):
    op = operations[i-1]
    next_num = numbers[i]
    
    if op == 'sum':
        result += next_num
    elif op == 'sub':
        result -= next_num
    elif op == 'mul':
        result *= next_num
    elif op == 'div':
        result /= next_num

# Приводим к целому числу
final_result = int(result)
print(f"Результат: {final_result}")
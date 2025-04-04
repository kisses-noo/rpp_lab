# Задание 1.2. Считать с клавиатуры три произвольных числа,
# вывести в консоль те числа, которые попадают в интервал.

valid_numbers = []

for i in range(3):
    user_input = input(f"Введите число {i + 1}: ")
    try:
        number = float(user_input)
        if 1 <= number <= 50:
            valid_numbers.append(number)
    except ValueError:
        print(f"Ошибка: '{user_input}' не является числом.")

if valid_numbers:
    print("Числа в интервале [1, 50]:", valid_numbers)
else:
    print("Нет чисел в интервале [1, 50].")


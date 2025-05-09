# Задание 1.4. Считать с клавиатуры непустую произвольную
# последовательность целых чисел.

# Считываем строку с клавиатуры.
string = input("Введите произвольную последовательность целых чисел: ")

# Хранение чисел последовательности.
sequence = []

# Переменная для хранения текущего числа.
num = ""
for character in string:
    # Если пробел, добавляем текущее число в последовательность.
    if character == ' ':
        if num:  # Если строка 'num' не пустая.
            try:
                # Добавляем число в последовательность, преобразуя его в int.
                sequence.append(int(num))
            except ValueError:
                print(f"Ошибка: '{num}' не является целым числом.")
            num = ""  # Сбрасываем текущее число.
    else:
        num += character  # Добавляем символ к текущему числу.

# Проверка на последнее число.
if num:
    try:
        sequence.append(int(num))
    except ValueError:
        print(f"Ошибка: '{num}' не является целым числом.")

# Проверка на пустую последовательность.
if not sequence:
    print("Ошибка: введена пустая последовательность")
else:
    # Находим количество чисел в последовательности.
    count = 0
    while count < len(sequence):
        count += 1
    print("Количество чисел в последовательности:", count)

    # Находим сумму всех чисел в последовательности.
    total_sum = 0
    j = 0  # Индекс для перебора чисел.
    while j < len(sequence):
        total_sum += sequence[j]
        j += 1
    print("Сумма всех чисел в последовательности:", total_sum)
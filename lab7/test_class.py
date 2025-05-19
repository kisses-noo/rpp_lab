import pytest
from triangle_class import Triangle, IncorrectTriangleSides

# Тест равностороннего треугольника и периметра
def test_equilateral():
    t = Triangle(3, 3, 3)
    assert t.triangle_type() == "equilateral"
    assert t.perimeter() == 9

# Тест равнобедренных треугольников и периметра
def test_isosceles():
    t1 = Triangle(3, 3, 4)
    t2 = Triangle(3, 4, 3)
    t3 = Triangle(4, 3, 3)
    assert t1.triangle_type() == "isosceles"
    assert t2.triangle_type() == "isosceles"
    assert t3.triangle_type() == "isosceles"
    assert t1.perimeter() == 10

# Тест разностороннего треугольника и периметра
def test_nonequilateral():
    t = Triangle(3, 4, 5)
    assert t.triangle_type() == "nonequilateral"
    assert t.perimeter() == 12

# Тест на некорректные типы данных
def test_incorrect_types():
    with pytest.raises(IncorrectTriangleSides):
        Triangle("3", 4, 5)

# Тест на отрицательные значения сторон
def test_negative_sides():
    with pytest.raises(IncorrectTriangleSides):
        Triangle(-3, 4, 5)

# Тест на нулевые значения сторон
def test_zero_sides():
    with pytest.raises(IncorrectTriangleSides):
        Triangle(0, 4, 5)

# Тест на невалидный треугольник (не выполняется неравенство треугольника)
def test_invalid_triangle():
    with pytest.raises(IncorrectTriangleSides):
        Triangle(1, 1, 10)

# Тест разностороннего треугольника с ошибкой в периметре        
def test_nonequilateral_failed():
    t = Triangle(4, 6, 7)
    assert t.triangle_type() == "nonequilateral"
    assert t.perimeter() == 11

# Тест равностороннего треугольника с ошибкой в типе данных 
def test_equilateral_failed():
    t = Triangle("3", 3, 3)
    assert t.triangle_type() == "equilateral"
    assert t.perimeter() == 10
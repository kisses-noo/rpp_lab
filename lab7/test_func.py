import unittest
from triangle_func import get_triangle_type, IncorrectTriangleSides

class TestTriangleFunc(unittest.TestCase):
    
    # Тест равностороннего треугольника
    def test_equilateral(self):
        self.assertEqual(get_triangle_type(3, 3, 3), "equilateral")
    
    # Тест равнобедренного треугольника
    def test_isosceles(self):
        self.assertEqual(get_triangle_type(3, 3, 4), "isosceles")
        self.assertEqual(get_triangle_type(3, 4, 3), "isosceles")
        self.assertEqual(get_triangle_type(4, 3, 3), "isosceles")
    
    # Тест разностороннего треугольника
    def test_nonequilateral(self):
        self.assertEqual(get_triangle_type(3, 4, 5), "nonequilateral")
    
    # Тест на некорректные типы данных
    def test_incorrect_types(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type("3", 4, 5)
    
    # Тест на отрицательные значения сторон
    def test_negative_sides(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(-3, 4, 5)
    
    # Тест на нулевые значения сторон
    def test_zero_sides(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(0, 4, 5)
    
    # Тест на невалидный треугольник (не выполняется неравенство треугольника)
    def test_invalid_triangle(self):
        with self.assertRaises(IncorrectTriangleSides):
            get_triangle_type(1, 1, 10)
    

if __name__ == '__main__':
    unittest.main()
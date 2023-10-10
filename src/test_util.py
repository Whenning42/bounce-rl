import unittest
from util import GrowingCircularFIFOArray, LinearInterpolator
from numpy import testing as npt

class TestLinearInterpolator(unittest.TestCase):
    def test_interpolation(self):
        interpolator = LinearInterpolator(0, 2, 0, 2)
        self.assertEqual(interpolator.get_value(0), 0)
        self.assertEqual(interpolator.get_value(1), 1)

    def test_extrapolation(self):
        extrapolator = LinearInterpolator(0, 1, 0, 1, extrapolate=True)
        self.assertEqual(extrapolator.get_value(-1), -1)
        self.assertEqual(extrapolator.get_value(2), 2)

        non_extrapolator = LinearInterpolator(0, 1, 0, 1, extrapolate=False)
        self.assertEqual(non_extrapolator.get_value(-1), 0)
        self.assertEqual(non_extrapolator.get_value(2), 1)

class TestGrowingCircularFIFOArray(unittest.TestCase):
    def test_loop_without_growth(self):
        buf = GrowingCircularFIFOArray(10)
        buf.push(1, 3)
        buf.push(2, 3)
        buf.push(3, 3)
        buf.push(4, 3)
        npt.assert_allclose(buf.get_array(), [4, 2, 3])

    def test_loop_with_growth(self):
        buf = GrowingCircularFIFOArray(10)
        buf.push(1, 3)
        buf.push(2, 3)
        buf.push(3, 3)
        buf.push(4, 4)
        npt.assert_allclose(buf.get_array(), [1, 2, 3, 4])

    def test_catch_decreased_size(self):
        buf = GrowingCircularFIFOArray(10)
        buf.push(1, 10)
        self.assertRaises(AssertionError, buf.push, 2, 9)

if __name__ == "__main__":
    unittest.main()
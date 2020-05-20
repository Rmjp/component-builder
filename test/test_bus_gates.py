import unittest

from compbuilder import Signal
from test.bus_gates import And2, And8

T = Signal.T
F = Signal.F

class TestAnd2(unittest.TestCase):
    def setUp(self):
        self.and2 = And2()

    def test_FFTT(self):
        self.assertEqual(self.and2.eval_single(a=Signal(1,2), b=Signal(3,2)),
                         Signal(1,2))

class TestAnd8(unittest.TestCase):
    def setUp(self):
        self.and8 = And8()

    def test_FFTT(self):
        self.assertEqual(self.and8.eval_single(a=Signal(0b11001100,8),
                                               b=Signal(0b10101010,8)),
                         Signal(0b10001000,8))

if __name__ == '__main__':
    unittest.main()

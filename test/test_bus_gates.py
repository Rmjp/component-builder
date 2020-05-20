import unittest

from compbuilder import Signal
from test.bus_gates import And2

T = Signal.T
F = Signal.F

class TestAnd2(unittest.TestCase):
    def setUp(self):
        self.and2 = And2()

    def test_create(self):
        pass

if __name__ == '__main__':
    unittest.main()

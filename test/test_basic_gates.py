import unittest

from compbuilder import Signal
from test.basic_gates import Nand, Not, And, Or, Xor, HalfAdder, FullAdder

T = Signal.T
F = Signal.F

class TestNandGate(unittest.TestCase):
    def setUp(self):
        self.nand = Nand()

    def test_input_FF(self):
        self.assertEqual(self.nand.eval_single(a=F, b=T), T)

    def test_input_FT(self):
        self.assertEqual(self.nand.eval_single(a=F, b=T), T)

    def test_input_TF(self):
        self.assertEqual(self.nand.eval_single(a=T, b=F), T)

    def test_input_TT(self):
        self.assertEqual(self.nand.eval_single(a=T, b=T), F)


class TestNotGate(unittest.TestCase):
    def setUp(self):
        self.not_gate = Not()

    def test_input_F(self):
        self.assertEqual(self.not_gate.eval_single(a=F), T)

    def test_input_T(self):
        self.assertEqual(self.not_gate.eval_single(a=T), F)


class TestOrGate(unittest.TestCase):
    def setUp(self):
        self.or_gate = Or()

    def test_input_FF(self):
        self.assertEqual(self.or_gate.eval_single(a=F, b=F), F)

    def test_input_FT(self):
        self.assertEqual(self.or_gate.eval_single(a=F, b=T), T)

    def test_input_TF(self):
        self.assertEqual(self.or_gate.eval_single(a=T, b=F), T)

    def test_input_TT(self):
        self.assertEqual(self.or_gate.eval_single(a=T, b=T), T)

        
class TestXorGate(unittest.TestCase):
    def setUp(self):
        self.xor_gate = Xor()

    def test_input_FF(self):
        self.assertEqual(self.xor_gate.eval_single(a=F, b=F), F)

    def test_input_FT(self):
        self.assertEqual(self.xor_gate.eval_single(a=F, b=T), T)

    def test_input_TF(self):
        self.assertEqual(self.xor_gate.eval_single(a=T, b=F), T)

    def test_input_TT(self):
        self.assertEqual(self.xor_gate.eval_single(a=T, b=T), F)

class TestAdder(unittest.TestCase):
    def setUp(self):
        self.half_adder = HalfAdder()
        self.full_adder = FullAdder()

    def test_half_adder(self):
        self.assertEqual(self.half_adder.eval(a=F, b=F), [F,F])
        self.assertEqual(self.half_adder.eval(a=F, b=T), [T,F])
        self.assertEqual(self.half_adder.eval(a=T, b=F), [T,F])
        self.assertEqual(self.half_adder.eval(a=T, b=T), [F,T])

    def test_full_adder(self):
        self.assertEqual(self.full_adder.eval(a=F, b=F, carry_in=F), [F,F])
        self.assertEqual(self.full_adder.eval(a=F, b=T, carry_in=F), [T,F])
        self.assertEqual(self.full_adder.eval(a=T, b=F, carry_in=F), [T,F])
        self.assertEqual(self.full_adder.eval(a=T, b=T, carry_in=F), [F,T])

        self.assertEqual(self.full_adder.eval(a=F, b=F, carry_in=T), [T,F])
        self.assertEqual(self.full_adder.eval(a=F, b=T, carry_in=T), [F,T])
        self.assertEqual(self.full_adder.eval(a=T, b=F, carry_in=T), [F,T])
        self.assertEqual(self.full_adder.eval(a=T, b=T, carry_in=T), [T,T])

        
if __name__ == '__main__':
    unittest.main()

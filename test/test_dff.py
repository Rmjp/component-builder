import unittest

from compbuilder import Signal, Component
from test.basic_gates import Nand, Not, DFF

from compbuilder import w

T = Signal.T
F = Signal.F

class TestDFF(unittest.TestCase):
    def setUp(self):
        self.dff = DFF()

    def test_sequence(self):
        self.assertEqual(self.dff.eval_single(d=T), F)
        self.assertEqual(self.dff.eval_single(d=F), T)
        self.assertEqual(self.dff.eval_single(d=F), F)
        self.assertEqual(self.dff.eval_single(d=T), F)
        self.assertEqual(self.dff.eval_single(d=T), T)
        self.assertEqual(self.dff.eval_single(d=F), T)
        self.assertEqual(self.dff.eval_single(d=F), F)

class FlipComp(Component):
    IN = []
    OUT = [w.out]

    PARTS = [
        DFF(d=w.a, q=w.out),
        Not(a=w.out, out=w.a)
    ]
    
class TestClockedComponent(unittest.TestCase):
    def setUp(self):
        self.flip = FlipComp()

    def test_flip(self):
        self.assertEqual(self.flip.eval_single(), F)
        self.assertEqual(self.flip.eval_single(), T)
        self.assertEqual(self.flip.eval_single(), F)
        self.assertEqual(self.flip.eval_single(), T)
        self.assertEqual(self.flip.eval_single(), F)
        self.assertEqual(self.flip.eval_single(), T)
        
        
if __name__ == '__main__':
    unittest.main()

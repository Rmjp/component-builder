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
    
class SeqComp1(Component):
    IN = [w.a]
    OUT = [w.out]

    PARTS = [
        DFF(d=w.a, q=w.out),
    ]
    
class SeqComp2(Component):
    IN = [w.a]
    OUT = [w.out]

    PARTS = [
        DFF(d=w.a, q=w.b),
        DFF(d=w.b, q=w.out),
    ]
    
class SeqComp3(Component):
    IN = [w.a]
    OUT = [w.out]

    PARTS = [
        DFF(d=w.a, q=w.b),
        DFF(d=w.b, q=w.c),
        Not(a=w.c, out=w.d),
        DFF(d=w.d, q=w.out),
    ]

class TestClockedComponent(unittest.TestCase):
    def setUp(self):
        self.flip = FlipComp()
        self.seq1 = SeqComp1()
        self.seq2 = SeqComp2()
        self.seq3 = SeqComp3()

    def test_flip(self):
        self.assertEqual(self.flip.eval_single(), F)
        self.assertEqual(self.flip.eval_single(), T)
        self.assertEqual(self.flip.eval_single(), F)
        self.assertEqual(self.flip.eval_single(), T)
        self.assertEqual(self.flip.eval_single(), F)
        self.assertEqual(self.flip.eval_single(), T)

    def test_seq1(self):
        self.assertEqual(self.seq1.eval_single(a=T), F)
        self.assertEqual(self.seq1.eval_single(a=F), T)
        self.assertEqual(self.seq1.eval_single(a=F), F)
        self.assertEqual(self.seq1.eval_single(a=T), F)
        self.assertEqual(self.seq1.eval_single(a=F), T)
        
    def test_seq2(self):
        self.assertEqual(self.seq2.eval_single(a=T), F)
        self.assertEqual(self.seq2.eval_single(a=F), F)
        self.assertEqual(self.seq2.eval_single(a=F), T)
        self.assertEqual(self.seq2.eval_single(a=T), F)
        self.assertEqual(self.seq2.eval_single(a=F), F)
        self.assertEqual(self.seq2.eval_single(a=F), T)
        self.assertEqual(self.seq2.eval_single(a=F), F)
        
    def test_seq3(self):
        self.assertEqual(self.seq3.eval_single(a=T), F)
        self.assertEqual(self.seq3.eval_single(a=F), T)
        self.assertEqual(self.seq3.eval_single(a=F), T)
        self.assertEqual(self.seq3.eval_single(a=T), F)
        self.assertEqual(self.seq3.eval_single(a=F), T)
        self.assertEqual(self.seq3.eval_single(a=F), T)
        self.assertEqual(self.seq3.eval_single(a=F), F)
        self.assertEqual(self.seq3.eval_single(a=F), T)
        
if __name__ == '__main__':
    unittest.main()

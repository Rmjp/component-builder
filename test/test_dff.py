import unittest

from compbuilder import Signal, Component
from test.basic_gates import Nand, Not, And, Or, DFF, FullAdder

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
        
class AutoCounter(Component):
    IN = [w(4).a]
    OUT = [w(4).out]

    PARTS = [
        Not(a=w(4).a[0], out=w.na0),
        And(a=w(4).a[0], b=w.na0, out=w.zero),
        Or(a=w(4).a[0], b=w.na0, out=w.one),
        FullAdder(a=w(4).a[0], b=w(4).q[0], carry_in=w.zero,
                  s=w(4).out[0], carry_out=w.adder0_carry_out),
        FullAdder(a=w(4).a[1], b=w(4).q[1], carry_in=w.adder0_carry_out,
                  s=w(4).out[1], carry_out=w.adder1_carry_out),
        FullAdder(a=w(4).a[2], b=w(4).q[2], carry_in=w.adder1_carry_out,
                  s=w(4).out[2], carry_out=w.adder2_carry_out),
        FullAdder(a=w(4).a[3], b=w(4).q[3], carry_in=w.adder2_carry_out,
                  s=w(4).out[3], carry_out=w.adder3_carry_out),
        DFF(d=w(4).out[0], q=w(4).q[0]),
        DFF(d=w(4).out[1], q=w(4).q[1]),
        DFF(d=w(4).out[2], q=w(4).q[2]),
        DFF(d=w(4).out[3], q=w(4).q[3]),
    ]
    
class TestClockedComponent(unittest.TestCase):
    def setUp(self):
        self.counter = AutoCounter()

    def test_auto_counter(self):
        for i in range(100):
            self.assertEqual(self.counter.eval_single(a=Signal(1,4)), Signal((i+1) % 16,4))

if __name__ == '__main__':
    unittest.main()

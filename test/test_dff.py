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
        self.assertEqual(self.dff.eval_single(In=T), F)
        self.assertEqual(self.dff.eval_single(In=F), T)
        self.assertEqual(self.dff.eval_single(In=F), F)
        self.assertEqual(self.dff.eval_single(In=T), F)
        self.assertEqual(self.dff.eval_single(In=T), T)
        self.assertEqual(self.dff.eval_single(In=F), T)
        self.assertEqual(self.dff.eval_single(In=F), F)

class FlipComp(Component):
    IN = []
    OUT = [w.out]

    PARTS = [
        DFF(In=w.a, out=w.out),
        Not(In=w.out, out=w.a)
    ]
    
class SeqComp1(Component):
    IN = [w.In]
    OUT = [w.out]

    PARTS = [
        DFF(In=w.In, out=w.out),
    ]
    
class SeqComp2(Component):
    IN = [w.In]
    OUT = [w.out]

    PARTS = [
        DFF(In=w.In, out=w.b),
        DFF(In=w.b, out=w.out),
    ]
    
class SeqComp3(Component):
    IN = [w.In]
    OUT = [w.out]

    PARTS = [
        DFF(In=w.In, out=w.b),
        DFF(In=w.b, out=w.c),
        Not(In=w.c, out=w.d),
        DFF(In=w.d, out=w.out),
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
        self.assertEqual(self.seq1.eval_single(In=T), F)
        self.assertEqual(self.seq1.eval_single(In=F), T)
        self.assertEqual(self.seq1.eval_single(In=F), F)
        self.assertEqual(self.seq1.eval_single(In=T), F)
        self.assertEqual(self.seq1.eval_single(In=F), T)
        
    def test_seq2(self):
        self.assertEqual(self.seq2.eval_single(In=T), F)
        self.assertEqual(self.seq2.eval_single(In=F), F)
        self.assertEqual(self.seq2.eval_single(In=F), T)
        self.assertEqual(self.seq2.eval_single(In=T), F)
        self.assertEqual(self.seq2.eval_single(In=F), F)
        self.assertEqual(self.seq2.eval_single(In=F), T)
        self.assertEqual(self.seq2.eval_single(In=F), F)
        
    def test_seq3(self):
        self.assertEqual(self.seq3.eval_single(In=T), F)
        self.assertEqual(self.seq3.eval_single(In=F), T)
        self.assertEqual(self.seq3.eval_single(In=F), T)
        self.assertEqual(self.seq3.eval_single(In=T), F)
        self.assertEqual(self.seq3.eval_single(In=F), T)
        self.assertEqual(self.seq3.eval_single(In=F), T)
        self.assertEqual(self.seq3.eval_single(In=F), F)
        self.assertEqual(self.seq3.eval_single(In=F), T)
        
class AutoCounter(Component):
    IN = [w(4).a]
    OUT = [w(4).out]

    PARTS = [
        FullAdder(a=w(4).a[0], b=w(4).q[0], carry_in=w.zero,
                  s=w(4).out[0], carry_out=w.adder0_carry_out),
        FullAdder(a=w(4).a[1], b=w(4).q[1], carry_in=w.adder0_carry_out,
                  s=w(4).out[1], carry_out=w.adder1_carry_out),
        FullAdder(a=w(4).a[2], b=w(4).q[2], carry_in=w.adder1_carry_out,
                  s=w(4).out[2], carry_out=w.adder2_carry_out),
        FullAdder(a=w(4).a[3], b=w(4).q[3], carry_in=w.adder2_carry_out,
                  s=w(4).out[3], carry_out=w.adder3_carry_out),
        DFF(In=w(4).out[0], out=w(4).q[0]),
        DFF(In=w(4).out[1], out=w(4).q[1]),
        DFF(In=w(4).out[2], out=w(4).q[2]),
        DFF(In=w(4).out[3], out=w(4).q[3]),
    ]
    
class AutoCounter1Bit(Component):
    IN = [w.a]
    OUT = [w(4).out]

    PARTS = [
        FullAdder(a=w.a, b=w(4).q[0], carry_in=w.zero,
                  s=w.out[0], carry_out=w.adder0_carry_out),
        FullAdder(a=w.zero, b=w.q[1], carry_in=w.adder0_carry_out,
                  s=w.out[1], carry_out=w.adder1_carry_out),
        FullAdder(a=w.zero, b=w.q[2], carry_in=w.adder1_carry_out,
                  s=w.out[2], carry_out=w.adder2_carry_out),
        FullAdder(a=w.zero, b=w.q[3], carry_in=w.adder2_carry_out,
                  s=w.out[3], carry_out=w.adder3_carry_out),
        DFF(In=w.out[0], out=w.q[0]),
        DFF(In=w.out[1], out=w.q[1]),
        DFF(In=w.out[2], out=w.q[2]),
        DFF(In=w.out[3], out=w.q[3]),
    ]
    
class TestCounter(unittest.TestCase):
    def setUp(self):
        self.counter = AutoCounter()
        self.counter_1bit = AutoCounter1Bit()

    def test_auto_counter(self):
        for i in range(100):
            self.assertEqual(self.counter.eval_single(a=Signal(1,4)), Signal((i+1) % 16,4))

    def test_auto_counter_1bit(self):
        for i in range(100):
            self.assertEqual(self.counter_1bit.eval_single(a=T), Signal((i+1) % 16,4))

if __name__ == '__main__':
    unittest.main()

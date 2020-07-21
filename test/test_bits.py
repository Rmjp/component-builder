import unittest

from compbuilder import Signal, Component
from test.basic_gates import Nand, Not, And, Or, DFF, FullAdder

from compbuilder import w
from compbuilder.tracing import trace

T = Signal.T
F = Signal.F

class Mux(Component):
    IN = [w.a, w.b, w.sel]
    OUT = [w.out]
    
    PARTS = [
        Not(In=w.sel, out=w.notsel),
        And(a=w.a, b=w.notsel, out=w.anotsel),
        And(a=w.b, b=w.sel, out=w.bsel),
        Or(a=w.anotsel, b=w.bsel, out=w.out),
    ]

class Bit(Component):
    IN = [w.In, w.load]
    OUT = [w.out]

    PARTS = [
        Mux(a=w.out, b=w.In, sel=w.load, out=w.dffin),
        DFF(In=w.dffin, out=w.out),
    ]

class Register2(Component):
    IN = [w(2).In, w.load]
    OUT = [w(2).out]

    PARTS = [
        Bit(In=w.In[0], load=w.load, out=w.out[0]),
        Bit(In=w.In[1], load=w.load, out=w.out[1]),
    ]


class Register16(Component):
    IN = [w(16).In, w.load]
    OUT = [w(16).out]

    PARTS = None

    def init_parts(self):
        if Register16.PARTS:
            return

        Register16.PARTS = []
        for i in range(16):
            Register16.PARTS.append(Bit(In=w.In[i], load=w.load, out=w.out[i]))


class TestBit(unittest.TestCase):
    def setUp(self):
        self.bit = Bit()

    def test_inputTrace(self):
        self.assertEqual(trace(self.bit, {'In':'11001101101011001', 'load':'10010000110101010'}, ['out']), {'out': '01110000010000110'})


class TestReg2(unittest.TestCase):
    def setUp(self):
        self.reg2 = Register2()

    def test_inputTrace_alwaysLoad(self):
        self.assertEqual(trace(self.reg2, {'In':[1,1,2,2,3,3,0,0,1], 'load':'111111111'}, ['out']),
                         {'out':[0,1,1,2,2,3,3,0,0]})

    def test_inputTrace(self):
        self.assertEqual(trace(self.reg2, {'In':[1,1,2,2,3,3,0,0,1], 'load':'010101010'}, ['out']),
                         {'out':[0,0,1,1,2,2,3,3,0]})


class TestReg16(unittest.TestCase):
    def setUp(self):
        self.reg16 = Register16()

    def test_inputTrace_alwaysLoad(self):
        self.assertEqual(trace(self.reg16, {'In':[131,2134,32767,65535,355,34234,0,10,0], 'load':'111111111'}, ['out']),
                         {'out':[0,131,2134,32767,65535,355,34234,0,10]})
        

if __name__ == '__main__':
    unittest.main()

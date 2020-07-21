import unittest

from compbuilder import Signal, Component, w
from test.visual_gates import (
        VisualComponent,
        Nand, Not, And, Or, Xor,
        DFF, FullAdder,
    )

T = Signal.T
F = Signal.F

################################################
class TestPrimitiveNand(unittest.TestCase):
    def setUp(self):
        self.nand = Nand()
        self.nand.flatten()

    def test_sequence(self):
        nand = self.nand
        self.assertEqual(nand.update(a=F,b=F)['out'], T)
        self.assertEqual(nand.update(a=F,b=T)['out'], T)
        self.assertEqual(nand.update(a=T,b=F)['out'], T)
        self.assertEqual(nand.update(a=T,b=T)['out'], F)
        self.nand.update(a=F,b=T)
        self.assertEqual(nand.update()['out'], T)
        self.assertEqual(nand.update(a=T)['out'], F)

################################################
class TestPrimitiveDFF(unittest.TestCase):
    def setUp(self):
        self.dff = DFF()
        self.dff.flatten()

    def test_sequence(self):
        dff = self.dff
        dff.update(In=F,clk=F)
        self.assertEqual(dff.update(clk=T)['out'], F) # triggered by rising edge
        self.assertEqual(dff.update(In=T)['out'], F)
        self.assertEqual(dff.update(clk=F)['out'], F) # ignore falling edge
        self.assertEqual(dff.update(clk=T)['out'], T) # triggered by rising edge
        dff.update(In=F)
        self.assertEqual(dff.update(clk=T)['out'], T) # must not change

################################################
class TestFlatComponent(unittest.TestCase):
    def setUp(self):
        self.xor = Xor()
        self.xor.flatten()

    def test_sequence(self):
        xor = self.xor
        self.assertEqual(xor.update(a=F,b=F)['out'], F)
        self.assertEqual(xor.update(a=F,b=T)['out'], T)
        self.assertEqual(xor.update(a=T,b=F)['out'], T)
        self.assertEqual(xor.update(a=T,b=T)['out'], F)
        self.xor.update(a=F,b=F)
        self.assertEqual(xor.update()['out'], F)
        self.assertEqual(xor.update(a=T)['out'], T)
        self.assertEqual(xor.update(b=T)['out'], F)

################################################
class DualClock(VisualComponent):
    IN = [w.In,w.clk1,w.clk2]
    OUT = [w.out]
    PARTS = [
        Xor(a=w.clk1,b=w.clk2,out=w.trig),
        DFF(In=w.In,clk=w.trig,out=w.out),
    ]

class TestFlatClockedComponent(unittest.TestCase):
    def setUp(self):
        self.comp = DualClock()
        self.comp.flatten()

    def test_sequence(self):
        comp = self.comp
        comp.update(In=F,clk1=F,clk2=F)
        self.assertEqual(comp.update(clk1=T)['out'],F)
        self.assertEqual(comp.update(In=T)['out'],F)
        self.assertEqual(comp.update(clk2=T)['out'],F)
        self.assertEqual(comp.update(clk1=F)['out'],T)

################################################
class Div2(VisualComponent):
    IN = [w.clk]
    OUT = [w.out]
    PARTS = [
        DFF(In=w.out1,clk=w.clk,out=w.out),
        Not(In=w.out,out=w.out1),
    ]

class Div4(VisualComponent):
    IN = [w.clk]
    OUT = [w.out]
    PARTS = [
        DFF(In=w.nout1,clk=w.clk,out=w.out1),
        Not(In=w.out1,out=w.nout1),
        DFF(In=w.nout2,clk=w.nout1,out=w.out),
        Not(In=w.out,out=w.nout2),
    ]

class TestFlatLoopedComponent(unittest.TestCase):
    def setUp(self):
        self.div2 = Div2()
        self.div4 = Div4()
        self.div2.flatten()
        self.div4.flatten()

    def test_sequence(self):
        div2 = self.div2
        # the latch and clock pin should be zero initially
        self.assertEqual(div2.update()['out'],F)
        self.assertEqual(div2.update(clk=F)['out'],F)
        self.assertEqual(div2.update(clk=T)['out'],T)
        self.assertEqual(div2.update(clk=F)['out'],T)
        self.assertEqual(div2.update(clk=T)['out'],F)
        self.assertEqual(div2.update(clk=F)['out'],F)
        self.assertEqual(div2.update(clk=T)['out'],T)
        self.assertEqual(div2.update(clk=F)['out'],T)
        self.assertEqual(div2.update(clk=T)['out'],F)

        div4 = self.div4
        # both latchs and clock pin should be zero initially
        self.assertEqual(div4.update()['out'],F)
        self.assertEqual(div4.update(clk=T)['out'],F)
        self.assertEqual(div4.update(clk=F)['out'],F)
        for i in range(5):
            self.assertEqual(div4.update(clk=T)['out'],T)
            self.assertEqual(div4.update(clk=F)['out'],T)
            self.assertEqual(div4.update(clk=T)['out'],T)
            self.assertEqual(div4.update(clk=F)['out'],T)
            self.assertEqual(div4.update(clk=T)['out'],F)
            self.assertEqual(div4.update(clk=F)['out'],F)
            self.assertEqual(div4.update(clk=T)['out'],F)
            self.assertEqual(div4.update(clk=F)['out'],F)

################################################
class Mem8(VisualComponent):
    IN = [w(8).In, w.clk]
    OUT = [w(8).out]
    PARTS = [
        DFF(In=w.In[0],out=w.out[0],clk=w.clk),
        DFF(In=w.In[1],out=w.out[1],clk=w.clk),
        DFF(In=w.In[2],out=w.out[2],clk=w.clk),
        DFF(In=w.In[3],out=w.out[3],clk=w.clk),
        DFF(In=w.In[4],out=w.out[4],clk=w.clk),
        DFF(In=w.In[5],out=w.out[5],clk=w.clk),
        DFF(In=w.In[6],out=w.out[6],clk=w.clk),
        DFF(In=w.In[7],out=w.out[7],clk=w.clk),
    ]

class TestFlatMultibitDFF(unittest.TestCase):
    def setUp(self):
        self.mem = Mem8()
        self.mem.flatten()

    def test_sequence(self):
        mem = self.mem
        mem.update(In=Signal(0xFF,8),clk=F)
        # all DFFs should be zero initially
        self.assertEqual(mem.update()['out'],Signal(0x00,8))
        self.assertEqual(mem.update(clk=T)['out'],Signal(0xFF,8))
        for i in range(256):
            mem.update(clk=F)
            self.assertNotEqual(mem.update(In=Signal(i,8))['out'],Signal(i,8))
            self.assertEqual(mem.update(clk=T)['out'],Signal(i,8))

################################################
class NotByConst(VisualComponent):
    IN = [w.In]
    OUT = [w.out]
    PARTS = [
        Nand(a=w.In, b=w.one, out=w.out),
    ]

class AndByConst(VisualComponent):
    IN = [w.a, w.b]
    OUT = [w.out]
    PARTS = [
        Nand(a=w.a, b=w.b, out=w.c),
        Nand(a=w.c, b=w.one, out=w.out),
    ]

class TestFlatConstant(unittest.TestCase):
    def setUp(self):
        self.not1 = NotByConst()
        self.and1 = AndByConst()
        self.not1.flatten()
        self.and1.flatten()

    def test_sequence(self):
        not1 = self.not1
        and1 = self.and1
        self.assertEqual(not1.update(In=F)['out'],T)
        self.assertEqual(not1.update(In=T)['out'],F)
        self.assertEqual(and1.update(a=F,b=F)['out'],F)
        self.assertEqual(and1.update(a=F,b=T)['out'],F)
        self.assertEqual(and1.update(a=T,b=F)['out'],F)
        self.assertEqual(and1.update(a=T,b=T)['out'],T)

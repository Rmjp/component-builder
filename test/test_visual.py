import unittest

from compbuilder import Signal, w
from compbuilder.visual import VisualMixin
from test.visual_gates import (
        VisualComponent as Component,
        Nand, Not, And, Or, Xor,
        DFF, FullAdder,
        And8
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
class And16(Component):
    IN = [w(16).a, w(16).b]
    OUT = [w(16).out]
    PARTS = [
        And8(a=w.a[0:8],b=w.b[0:8],out=w.out[0:8]),
        And8(a=w.a[8:16],b=w.b[8:16],out=w.out[8:16]),
    ]

class TestRelativeSlice(unittest.TestCase):
    def setUp(self):
        self.and16 = And16()
        self.and16.flatten()

    def test_sequence(self):
        import random
        and16 = self.and16
        for i in range(100):
            a = random.randint(0,65535)
            b = random.randint(0,65535)
            self.assertEqual(and16.update(a=Signal(a,16),b=Signal(b,16))['out'],Signal(a&b,16))

################################################
class Buffer(Component):
  IN = [w.In]
  OUT = [w.out]

  PARTS = [
      And(a=w.In, b=w.one, out=w.out),
  ]

class ChainedDFF(Component):
    IN = [w.In, w.clk]
    OUT = [w.out1, w.out2, w.out3]

    PARTS = [
        Buffer(In=w.In, out=w.out1),
        DFF(In=w.In, out=w.out2, clk=w.clk),
        DFF(In=w.out2, out=w.out3, clk=w.clk),
    ]

class TestFlatChainedDFF(unittest.TestCase):
    def setUp(self):
        self.comp = ChainedDFF()
        self.comp.flatten()

    def test_sequence(self):
        comp = self.comp
        comp.update(In=F,clk=F)
        self.assertEqual(comp.update(clk=T),{'out1':F, 'out2':F, 'out3':F})
        comp.update(In=T)
        self.assertEqual(comp.update(clk=F),{'out1':T, 'out2':F, 'out3':F})
        self.assertEqual(comp.update(clk=T),{'out1':T, 'out2':T, 'out3':F})
        self.assertEqual(comp.update(clk=F),{'out1':T, 'out2':T, 'out3':F})
        self.assertEqual(comp.update(clk=T),{'out1':T, 'out2':T, 'out3':T})

        comp.update(In=F)
        self.assertEqual(comp.update(clk=F),{'out1':F, 'out2':T, 'out3':T})
        self.assertEqual(comp.update(clk=T),{'out1':F, 'out2':F, 'out3':T})
        self.assertEqual(comp.update(clk=F),{'out1':F, 'out2':F, 'out3':T})
        self.assertEqual(comp.update(clk=T),{'out1':F, 'out2':F, 'out3':F})
        self.assertEqual(comp.update(clk=F),{'out1':F, 'out2':F, 'out3':F})


################################################
class DualClock(Component):
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
class Div2(Component):
    IN = [w.clk]
    OUT = [w.out]
    PARTS = [
        DFF(In=w.out1,clk=w.clk,out=w.out),
        Not(In=w.out,out=w.out1),
    ]

class Div4(Component):
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
class Mem8(Component):
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
class NotByConst(Component):
    IN = [w.In]
    OUT = [w.out]
    PARTS = [
        Nand(a=w.In, b=w.one, out=w.out),
    ]

class AndByConst(Component):
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

################################################
class Mem8NoClk(Component):
    IN = [w(8).In]
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

class TestFlatMultibitDFFNoClk(unittest.TestCase):
    def setUp(self):
        self.mem = Mem8()
        self.mem.add_clk_wire()
        self.mem.flatten()

    def test_clk_added(self):
        self.assertTrue('clk' in self.mem._generate_part_config())

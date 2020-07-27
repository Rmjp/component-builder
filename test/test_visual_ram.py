import unittest

from compbuilder import Signal, Component, w
from test.visual_gates import (
        VisualComponent,
        Nand, Buffer, Not, And, Or, Xor,
        DFF, FullAdder,
        And8
    )

T = Signal.T
F = Signal.F

################################################
class Mux(Component):
    IN = [w.a, w.b, w.sel]
    OUT = [w.out]

    PARTS = [
        Not(In=w.sel, out=w.notsel),
        And(a=w.a, b=w.notsel, out=w.o1),
        And(a=w.sel, b=w.b, out=w.o2),
        Or(a=w.o1, b=w.o2, out=w.out)
    ]

class Mux16(Component):
    IN = [w(16).a, w(16).b, w.sel]
    OUT = [w(16).out]

    PARTS = None

    def init_parts(self):
        if Mux16.PARTS:
            return

        Mux16.PARTS = []
        for i in range(16):
            Mux16.PARTS.append(Mux(a=w.a[i], b=w.b[i], sel=w.sel, out=w.out[i]))

class Mux4Way16(Component):
    IN = [w(16).a, w(16).b, w(16).c, w(16).d, w(2).sel]
    OUT = [w(16).out]

    PARTS = [
        Mux16(a=w.a, b=w.b, sel=w.sel[0], out=w(16).o1),
        Mux16(a=w.c, b=w.d, sel=w.sel[0], out=w(16).o2),
        Mux16(a=w.o1, b=w.o2, sel=w.sel[1], out=w.out)
    ]

class Mux8Way16(Component):
    IN = [
        w(16).a,
        w(16).b,
        w(16).c,
        w(16).d,
        w(16).e,
        w(16).f,
        w(16).g,
        w(16).h,
        w(3).sel,
    ]
    OUT = [w(16).out]

    PARTS = [
        Mux4Way16(a=w.a, b=w.b, c=w.c, d=w.d, sel=w.sel[:2], out=w(16).o1),
        Mux4Way16(a=w.e, b=w.f, c=w.g, d=w.h, sel=w.sel[:2], out=w(16).o2),
        Mux16(a=w.o1, b=w.o2, sel=w.sel[2], out=w.out)
    ]


class DMux(Component):
    IN = [w.In, w.sel]
    OUT = [w.a, w.b]

    PARTS = [
        Not(In=w.sel, out=w.notsel),
        And(a=w.In, b=w.notsel, out=w.a),
        And(a=w.In, b=w.sel, out=w.b)
    ]

class DMux4Way(Component):
    IN = [w.In, w(2).sel]
    OUT = [w.a, w.b, w.c, w.d]

    PARTS = [
        DMux(In=w.In, sel=w.sel[1], a=w.o1, b=w.o2),
        DMux(In=w.o1, sel=w.sel[0], a=w.a, b=w.b),
        DMux(In=w.o2, sel=w.sel[0], a=w.c, b=w.d)
    ]


class DMux8Way(Component):
    IN = [w.In, w(3).sel]
    OUT = [w.a, w.b, w.c, w.d, w.e, w.f, w.g, w.h]

    PARTS = [
        DMux(In=w.In, sel=w.sel[2], a=w.o1, b=w.o2),
        DMux4Way(In=w.o1, sel=w.sel[:2], a=w.a, b=w.b, c=w.c, d=w.d),
        DMux4Way(In=w.o2, sel=w.sel[:2], a=w.e, b=w.f, c=w.g, d=w.h)
    ]

class Bit(VisualComponent):
    IN = [w.In, w.load, w.clk]
    OUT = [w.out]

    PARTS = [
        Mux(a=w.out, b=w.In, sel=w.load, out=w.data),
        DFF(In=w.data, out=w.out, clk=w.clk)
    ]

class Register(VisualComponent):
    IN = [w(16).In, w.load, w.clk]
    OUT = [w(16).out]

    PARTS = None

    def init_parts(self):
        if Register.PARTS:
            return

        Register.PARTS = []
        for i in range(16):
            Register.PARTS.append(
                Bit(In=w.In[i], load=w.load, out=w.out[i], clk=w.clk)
            )

class RAM8(VisualComponent):
    IN = [w(16).In, w(3).address, w.load, w.clk]
    OUT = [w(16).out]

    PARTS = [
        DMux8Way(In=w.load, sel=w.address, a=w.ld0, b=w.ld1, c=w.ld2, d=w.ld3, e=w.ld4, f=w.ld5, g=w.ld6, h=w.ld7),
        Register(In=w.In, load=w.ld0, out=w(16).o0, clk=w.clk),
        Register(In=w.In, load=w.ld1, out=w(16).o1, clk=w.clk),
        Register(In=w.In, load=w.ld2, out=w(16).o2, clk=w.clk),
        Register(In=w.In, load=w.ld3, out=w(16).o3, clk=w.clk),
        Register(In=w.In, load=w.ld4, out=w(16).o4, clk=w.clk),
        Register(In=w.In, load=w.ld5, out=w(16).o5, clk=w.clk),
        Register(In=w.In, load=w.ld6, out=w(16).o6, clk=w.clk),
        Register(In=w.In, load=w.ld7, out=w(16).o7, clk=w.clk),
        Mux8Way16(a=w.o0, b=w.o1, c=w.o2, d=w.o3, e=w.o4, f=w.o5, g=w.o6, h=w.o7, sel=w.address, out=w.out),
    ]

class TestFlatRAM8(unittest.TestCase):
    def setUp(self):
        self.ram = RAM8()
        self.ram.flatten()

    def test_sequence(self):
        from random import randint
        ram = self.ram

        rands = {}
        for i in range(10):
            addr = randint(0,7)
            data = randint(0,65535)
            rands[addr] = data
            ram.update(clk=F)
            ram.update(address=Signal(addr,3),In=Signal(data,16),load=T)
            ram.update(clk=T)
            ram.update(clk=F)

        for addr,data in rands.items():
            self.assertEqual(ram.update(address=Signal(addr,3))['out'],Signal(data,16))

#####################################
class Bus3(Component):
    IN = [w.In0, w.In1, w.In2]
    OUT = [w(3).out]

    PARTS = [
        Buffer(In=w.In0, out=w.out[0]),
        Buffer(In=w.In1, out=w.out[1]),
        Buffer(In=w.In2, out=w.out[2]),
    ]

class RAM64(Component):
    IN = [w(16).In, w(6).address, w.load, w.clk]
    OUT = [w(16).out]

    PARTS = [
        Bus3(In0=w.address[0], In1=w.address[1], In2=w.address[2], out=w(3).addr012),
        Bus3(In0=w.address[3], In1=w.address[4], In2=w.address[5], out=w(3).addr345),
        DMux8Way(In=w.load, sel=w.addr345, a=w.ld0, b=w.ld1, c=w.ld2, d=w.ld3, e=w.ld4, f=w.ld5, g=w.ld6, h=w.ld7),
        RAM8(In=w.In, address=w.addr012, load=w.ld0, out=w(16).o0, clk=w.clk),
        RAM8(In=w.In, address=w.addr012, load=w.ld1, out=w(16).o1, clk=w.clk),
        RAM8(In=w.In, address=w.addr012, load=w.ld2, out=w(16).o2, clk=w.clk),
        RAM8(In=w.In, address=w.addr012, load=w.ld3, out=w(16).o3, clk=w.clk),
        RAM8(In=w.In, address=w.addr012, load=w.ld4, out=w(16).o4, clk=w.clk),
        RAM8(In=w.In, address=w.addr012, load=w.ld5, out=w(16).o5, clk=w.clk),
        RAM8(In=w.In, address=w.addr012, load=w.ld6, out=w(16).o6, clk=w.clk),
        RAM8(In=w.In, address=w.addr012, load=w.ld7, out=w(16).o7, clk=w.clk),
        Mux8Way16(a=w.o0, b=w.o1, c=w.o2, d=w.o3, e=w.o4, f=w.o5, g=w.o6, h=w.o7, sel=w.addr345, out=w.out),
    ]

class TestFlatRAM64(unittest.TestCase):
    def setUp(self):
        self.ram = RAM64()
        self.ram.flatten()

    def test_sequence(self):
        from random import randint
        ram = self.ram

        rands = {}
        for i in range(10):
            addr = randint(0,63)
            data = randint(0,65535)
            rands[addr] = data
            ram.update(clk=F)
            ram.update(address=Signal(addr,6),In=Signal(data,16),load=T)
            ram.update(clk=T)
            ram.update(clk=F)

        for addr,data in rands.items():
            self.assertEqual(ram.update(address=Signal(addr,6))['out'],Signal(data,16))

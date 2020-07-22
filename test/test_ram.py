import unittest

from compbuilder import Signal, Component
from test.basic_gates import Nand, Not, And, Or, DFF, FullAdder, HalfAdder, Xor

from compbuilder import w
from compbuilder.tracing import trace, report_parts

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
        Mux16(a=w.a, b=w.b, sel=w.sel[0], out=w(16).aORb),
        Mux16(a=w.c, b=w.d, sel=w.sel[0], out=w(16).cORd),
        Mux16(a=w.aORb, b=w.cORd, sel=w.sel[1], out=w.out),
    ]

class Mux8Way16(Component):
    IN = [w(16).a, w(16).b, w(16).c, w(16).d, 
          w(16).e, w(16).f, w(16).g, w(16).h, w(3).sel]
    OUT = [w(16).out]

    PARTS = [
        Mux4Way16(a=w.a, b=w.b, c=w.c, d=w.d, sel=w.sel[0:2], out=w(16).choice1),
        Mux4Way16(a=w.e, b=w.f, c=w.g, d=w.h, sel=w.sel[0:2], out=w(16).choice2),
        Mux16(a=w.choice1, b=w.choice2, sel=w.sel[2], out=w.out),
    ]

class DMux(Component):
    IN = [w.In, w.sel]
    OUT = [w.a, w.b]
    
    PARTS = [
        Not(In=w.sel, out=w.notsel),
        And(a=w.In, b=w.notsel, out=w.a),
        And(a=w.In, b=w.sel, out=w.b),
    ]

class DMux4Way(Component):
    IN = [w.In, w(2).sel]
    OUT = [w.a, w.b, w.c, w.d]
    
    PARTS = [
        DMux(In=w.In, sel=w.sel[1], a=w.aORb, b=w.cORd),
        DMux(In=w.aORb, sel=w.sel[0], a=w.a, b=w.b),
        DMux(In=w.cORd, sel=w.sel[0], a=w.c, b=w.d),
    ]

class DMux8Way(Component):
    IN = [w.In, w(3).sel]
    OUT = [w.a, w.b, w.c, w.d, w.e, w.f, w.g, w.h]
    
    PARTS = [
        DMux(In=w.In, sel=w.sel[2], a=w.abcd, b=w.efgh),
        DMux4Way(In=w.abcd, sel=w.sel[0:2], a=w.a, b=w.b, c=w.c, d=w.d),
        DMux4Way(In=w.efgh, sel=w.sel[0:2], a=w.e, b=w.f, c=w.g, d=w.h),
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

class Register(Component):
    IN = [w(16).In, w.load]
    OUT = [w(16).out]

    PARTS = None

    def init_parts(self):
        if Register.PARTS:
            return

        Register.PARTS = []
        for i in range(16):
            Register.PARTS.append(Bit(In=w.In[i], load=w.load, out=w.out[i]))

class RAM8(Component):
    IN = [w(16).In, w(3).address, w.load]
    OUT = [w(16).out]

    PARTS = [
        DMux8Way(In=w.load, sel=w.address, a=w.ld0, b=w.ld1, c=w.ld2, d=w.ld3, e=w.ld4, f=w.ld5, g=w.ld6, h=w.ld7),
        Register(In=w.In, load=w.ld0, out=w(16).o0),
        Register(In=w.In, load=w.ld1, out=w(16).o1),
        Register(In=w.In, load=w.ld2, out=w(16).o2),
        Register(In=w.In, load=w.ld3, out=w(16).o3),
        Register(In=w.In, load=w.ld4, out=w(16).o4),
        Register(In=w.In, load=w.ld5, out=w(16).o5),
        Register(In=w.In, load=w.ld6, out=w(16).o6),
        Register(In=w.In, load=w.ld7, out=w(16).o7),
        Mux8Way16(a=w.o0, b=w.o1, c=w.o2, d=w.o3, e=w.o4, f=w.o5, g=w.o6, h=w.o7, sel=w.address, out=w.out),
    ]

class Goto(Component):
    IN = [w.In]
    OUT = [w.out]

    PARTS = [
        And(a=w.In, b=w.T, out=w.out),
    ]

class Bus3(Component):
    IN = [w.In0, w.In1, w.In2]
    OUT = [w(3).out]

    PARTS = [
        Goto(In=w.In0, out=w.out[0]),
        Goto(In=w.In1, out=w.out[1]),
        Goto(In=w.In2, out=w.out[2]),
    ]

class RAM64(Component):
    IN = [w(16).In, w(6).address, w.load]
    OUT = [w(16).out]

    PARTS = [
        Bus3(In0=w.address[0], In1=w.address[1], In2=w.address[2], out=w(3).addr012),
        Bus3(In0=w.address[3], In1=w.address[4], In2=w.address[5], out=w(3).addr345),
        DMux8Way(In=w.load, sel=w.addr345, a=w.ld0, b=w.ld1, c=w.ld2, d=w.ld3, e=w.ld4, f=w.ld5, g=w.ld6, h=w.ld7),
        RAM8(In=w.In, address=w.addr012, load=w.ld0, out=w(16).o0),
        RAM8(In=w.In, address=w.addr012, load=w.ld1, out=w(16).o1),
        RAM8(In=w.In, address=w.addr012, load=w.ld2, out=w(16).o2),
        RAM8(In=w.In, address=w.addr012, load=w.ld3, out=w(16).o3),
        RAM8(In=w.In, address=w.addr012, load=w.ld4, out=w(16).o4),
        RAM8(In=w.In, address=w.addr012, load=w.ld5, out=w(16).o5),
        RAM8(In=w.In, address=w.addr012, load=w.ld6, out=w(16).o6),
        RAM8(In=w.In, address=w.addr012, load=w.ld7, out=w(16).o7),
        Mux8Way16(a=w.o0, b=w.o1, c=w.o2, d=w.o3, e=w.o4, f=w.o5, g=w.o6, h=w.o7, sel=w.addr345, out=w.out),
    ]

class TestRam(unittest.TestCase):
    def test1(self):
        andgate = And()
        print(andgate.eval(a=T, b=F))
        
        return
        trace(
            ram64, 
            {'In':[0,0,10,10,10,3,3,3,7,7,7,7,32769,32769,32769,32769,32769,32769,32769,32769,32769,15,15,32769,15,15,32769,15,15,32769,15,15,32769,15,15,32769,15,15,32769,15,15,32769,15,15,32769,32769],
             'load':[0,1,0,1,0,0,1,0,0,1,0,0,1,1,1,1,1,1,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,0],
             'address':[0,0,0,1,0,3,3,3,1,7,7,0,0,1,2,3,4,5,6,7,0,0,0,0,1,0,1,2,0,2,3,0,3,4,0,4,5,0,5,6,0,6,7,0,7,0]
            },
            ['out']
        )

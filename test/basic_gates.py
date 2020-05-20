from compbuilder import Component, Signal

from compbuilder import w

class Nand(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = []

    def process(self, a, b):
        if (a.get()==1) and (b.get()==1):
            return [Signal(0)]
        else:
            return [Signal(1)]

class Not(Component):
    IN = [w.a]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.a, b=w.a, out=w.out),
    ]

class And(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.a, b=w.b, out=w.c),
        Not(a=w.c, out=w.out),
    ]

class Or(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Not(a=w.a, out=w.na),
        Not(a=w.b, out=w.nb),
        Nand(a=w.na, b=w.nb, out=w.out),
    ]

class Xor(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Not(a=w.a, out=w.na),
        Not(a=w.b, out=w.nb),
        And(a=w.a, b=w.nb, out=w.and1),
        And(a=w.b, b=w.na, out=w.and2),
        Or(a=w.and1, b=w.and2, out=w.out),
    ]

class HalfAdder(Component):
    IN = [w.a, w.b]
    OUT = [w.s, w.carry]

    PARTS = [
        Xor(a=w.a, b=w.b, out=w.s),
        And(a=w.a, b=w.b, out=w.carry),
    ]
    
class FullAdder(Component):
    IN = [w.a, w.b, w.carry_in]
    OUT = [w.s, w.carry_out]

    PARTS = [
        HalfAdder(a=w.a,
                  b=w.b,
                  s=w.s1,
                  carry=w.c1),
        HalfAdder(a=w.carry_in,
                  b=w.s1,
                  s=w.s,
                  carry=w.c2),
        Or(a=w.c1,
           b=w.c2,
           out=w.carry_out),
    ]


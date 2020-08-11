from compbuilder import Component, Signal
from compbuilder import w

from .basic_gates import Nand, And

class And2(Component):
    IN = [w(2).a, w(2).b]
    OUT = [w(2).out]

    PARTS = [
        And(a=w.a[0], b=w.b[0],
             out=w.out[0]),
        And(a=w.a[1], b=w.b[1],
             out=w.out[1]),
    ]

class And8(Component):
    IN = [w(8).a, w(8).b]
    OUT = [w(8).out]

    PARTS = None

    def init_parts(self):
        if And8.PARTS:
            return

        And8.PARTS = []
        for i in range(8):
            And8.PARTS.append(And(a=w.a[i], b=w.b[i],
                                  out=w.out[i]))

class AndWith12(Component):
    IN = [w(8).In]
    OUT = [w(8).out]

    PARTS = [
        And8(a=w.In, b=w(8).constant(12), out=w.out),
    ]

        

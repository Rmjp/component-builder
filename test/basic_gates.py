from compbuilder import Component, Signal

from compbuilder import w

# Two primitive gates - Nand and DFF

class Nand(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = []

    def process(self, a, b):
        if (a.get()==1) and (b.get()==1):
            return {'out': Signal(0)}
        else:
            return {'out': Signal(1)}

class DFF(Component):
    IN = [w.In]
    OUT = [w.out]

    PARTS = []

    def __init__(self, **kwargs):
        super(DFF, self).__init__(**kwargs)
        self.is_clocked_component = True
        self.saved_input_kwargs = None
    
    def process(self, In=None):
        if self.saved_input_kwargs == None:
            self.saved_output = {'out': Signal(0)}
        else:
            self.saved_output = {'out': self.saved_input_kwargs['In']}
        return self.saved_output

    def prepare_process(self, In):
        self.saved_input_kwargs = {'In': In}


class Not(Component):
    IN = [w.In]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.In, b=w.In, out=w.out),
    ]

class And(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.a, b=w.b, out=w.c),
        Not(In=w.c, out=w.out),
    ]

class Or(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Not(In=w.a, out=w.na),
        Not(In=w.b, out=w.nb),
        Nand(a=w.na, b=w.nb, out=w.out),
    ]

class Xor(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Not(In=w.a, out=w.na),
        Not(In=w.b, out=w.nb),
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


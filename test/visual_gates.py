from compbuilder import Component, Signal
from compbuilder import w
from compbuilder.visual import VisualMixin

class Nand(VisualMixin,Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = []

    LAYOUT_CONFIG = {
        'width' : 60,
        'height' : 50,
        'port_width' : 0,
        'port_height' : 0,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 25
                     a 25,25,180,1,1,0,50
                     h -25
                     z"/>
            <circle cx="55" cy="25" r="5"/>
        """,
    }

    def process(self, a, b):
        if (a.get()==1) and (b.get()==1):
            return [Signal(0)]
        else:
            return [Signal(1)]
    process.js = {
        'out' : 'return (w.a==1) && (w.b==1) ? 0 : 1;',
    }


class Not(VisualMixin,Component):
    IN = [w.a]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.a, b=w.a, out=w.out),
    ]


class And(VisualMixin,Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.a, b=w.b, out=w.c),
        Not(a=w.c, out=w.out),
    ]

    LAYOUT_CONFIG = {
        'width' : 50,
        'height' : 50,
        'port_width' : 0,
        'port_height' : 0,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 25
                     a 25,25,180,1,1,0,50
                     h -25
                     z" />
        """,
    }


class Or(VisualMixin,Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Not(a=w.a, out=w.na),
        Not(a=w.b, out=w.nb),
        Nand(a=w.na, b=w.nb, out=w.out),
    ]


class Xor(VisualMixin,Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Not(a=w.a, out=w.na),
        Not(a=w.b, out=w.nb),
        And(a=w.a, b=w.nb, out=w.and1),
        And(a=w.b, b=w.na, out=w.and2),
        Or(a=w.and1, b=w.and2, out=w.out),
    ]


class HalfAdder(VisualMixin,Component):
    IN = [w.a, w.b]
    OUT = [w.s, w.carry]

    PARTS = [
        Xor(a=w.a, b=w.b, out=w.s),
        And(a=w.a, b=w.b, out=w.carry),
    ]
    

class FullAdder(VisualMixin,Component):
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


class And8(VisualMixin,Component):
    IN = [w(8).a, w(8).b]
    OUT = [w(8).out]

    PARTS = None

    def init_parts(self):
        if And8.PARTS:
            return

        And8.PARTS = []
        for i in range(8):
            And8.PARTS.append(And(a=w(8).a[i], b=w(8).b[i],
                                  out=w(8).out[i]))

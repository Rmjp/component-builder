from compbuilder import Component, Signal
from compbuilder import w
from compbuilder.visual import VisualMixin

class Nand(VisualMixin,Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = []

    LAYOUT_CONFIG = {
        'width' : 48,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        #'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 20
                     a 20,20,180,1,1,0,40
                     h -20
                     z" />
            <circle cx="44" cy="20" r="4"/>
        """,
    }

    def process(self, a, b):
        if (a.get()==1) and (b.get()==1):
            return {'out': Signal(0)}
        else:
            return {'out': Signal(1)}
    process.js = {
        'out' : 'function(w) { return (w.a==1) && (w.b==1) ? 0 : 1; }',
    }


class Not(VisualMixin,Component):
    IN = [w.a]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.a, b=w.a, out=w.out),
    ]

    LAYOUT_CONFIG = {
        'width' : 38,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 0,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     l 30,20
                     l -30,20
                     z" />
            <circle cx="34" cy="20" r="4"/>
        """,
    }


class And(VisualMixin,Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = [
        Nand(a=w.a, b=w.b, out=w.c),
        Not(a=w.c, out=w.out),
    ]

    LAYOUT_CONFIG = {
        'width' : 40,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 20
                     a 20,20,180,1,1,0,40
                     h -20
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

    LAYOUT_CONFIG = {
        'width' : 40,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 0,0
                     h 5
                     q 25,0,35,20
                     q -10,20,-35,20
                     h -5
                     Q 10,20,0,0
                     z
                     M 0,10.5 h 4
                     M 0,29.5 h 4
                     " />
        """,
    }


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

    LAYOUT_CONFIG = {
        'width' : 45,
        'height' : 40,
        'port_width' : 0,
        'port_height' : 16,
        'label' : '',
        'ports' : {  # hide all port labels
            'a' : {'label' : ''},
            'b' : {'label' : ''},
            'out' : {'label' : ''},
        },
        'svg' : """
            <path d="M 5,0
                     h 5
                     q 25,0,35,20
                     q -10,20,-35,20
                     h -5
                     q 10,-20,0,-40
                     z
                     M 0,40" />
            <path d="M 0,0
                     q 10,20,0,40
                     M 0,10.5 h 4
                     M 0,29.5 h 4" style="fill:none"/>
        """,
    }

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


class And2(VisualMixin,Component):
    IN = [w(2).a, w(2).b]
    OUT = [w(2).out]

    PARTS = [
        And(a=w(2).a[0], b=w(2).b[0],
             out=w(2).out[0]),
        And(a=w(2).a[1], b=w(2).b[1],
             out=w(2).out[1]),
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


class DFF(VisualMixin,Component):
    IN = [w.d,w.clk]
    OUT = [w.q]

    PARTS = []
    TRIGGER = [w.clk]
    LATCH = [w.q]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._clk = Signal(0) 
        self._q = Signal(0)
        self.is_clocked_component = True
    
    def process(self,d,clk):
        if self._clk.get() == 0 and clk.get() == 1:
            self._q = d
        self._clk = clk
        return {'q':self._q}
    process.js = {
        'q' : '''
            function(w,s) { // wires,states
              if (s.clk == 0 && w.clk == 1)
                s.q = w.d;
              s.clk = w.clk;
              return s.q;
            }''',
    }

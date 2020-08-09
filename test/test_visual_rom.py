import unittest
import json

from compbuilder import Signal, w
import compbuilder.flatten
from compbuilder.visual import VisualMixin
from test.visual_gates import VisualComponent as Component

T = Signal.T
F = Signal.F

################################################
def gen_fast_rom_component(address_size,name,data):

    class FastROM(Component):
        IN = [w(address_size).address]
        OUT = [w(16).out]

        PARTS = []

        DATA = data

        def __init__(self,**kwargs):
            super().__init__(**kwargs)

        __init__.js = '''
            function(s) {{
              s.data = {};
            }}
        '''.format(json.dumps(DATA))

        def process(self,address):
            a = address.get()
            if a < len(data) and a < 2**address_size:
                return {'out': Signal(self.DATA[a],16)}
            else:
                return {'out': Signal(0,16)}

        process_interact = process
        process_interact.js = {
            'out' : '''
                function(w,s) { // wires,states
                  return s.data[w.address];
                }''',
        }

    FastROM.__name__ = name
    return FastROM

class TestFastROM(unittest.TestCase):
    def setUp(self):
        self.data = [0x0000,0xffff,0x0001,0x0002,0x1000]
        ROM1 = gen_fast_rom_component(3,'ROM1',self.data)
        self.rom1 = ROM1()
        self.rom1.flatten()

    def test_sequence(self):
        rom1 = self.rom1
        for addr,data in enumerate(self.data):
            self.assertEqual(rom1.update(address=Signal(addr,3))['out'],
                             Signal(data,16))
        self.assertEqual(rom1.update(address=Signal(len(self.data)+1,3))['out'],
                         Signal(0,16))

import unittest

from compbuilder import Signal, Component, w
from test.basic_gates import Nand, Not, And, Or, Xor, HalfAdder, FullAdder, DFF

T = Signal.T
F = Signal.F

from compbuilder.tracing import report_parts, trace

class TestReportParts(unittest.TestCase):
    def setUp(self):
        self.not_gate = Not()
        self.and_gate = And()
        self.xor_gate = Xor()

    def test_gate_name(self):
        self.assertEqual(self.not_gate.get_gate_name(), 'Not')
        self.assertEqual(self.and_gate.get_gate_name(), 'And')
        self.assertEqual(self.xor_gate.get_gate_name(), 'Xor')

    def test_list_parts_1level(self):
        expected_not_output = """
Not
  Nand-1
""".strip()
        
        expected_and_output = """
And
  Nand-1
  Not-2
""".strip()
        
        expected_xor_output = """
Xor
  Not-1
  Not-2
  And-3
  And-4
  Or-5
""".strip()
        
        self.assertEqual(report_parts(self.not_gate).split('\n'),
                         expected_not_output.split('\n'))
        self.assertEqual(report_parts(self.and_gate).split('\n'),
                         expected_and_output.split('\n'))
        self.assertEqual(report_parts(self.xor_gate).split('\n'),
                         expected_xor_output.split('\n'))

    def test_list_parts_2levels(self):
        expected_not_output = """
Not
  Nand-1
""".strip()
        
        expected_and_output = """
And
  Nand-1
  Not-2
    Nand-2-1
""".strip()
        
        expected_xor_output = """
Xor
  Not-1
    Nand-1-1
  Not-2
    Nand-2-1
  And-3
    Nand-3-1
    Not-3-2
  And-4
    Nand-4-1
    Not-4-2
  Or-5
    Not-5-1
    Not-5-2
    Nand-5-3
""".strip()
        
        self.assertEqual(report_parts(self.not_gate, level=2).split('\n'),
                         expected_not_output.split('\n'))
        self.assertEqual(report_parts(self.and_gate, level=2).split('\n'),
                         expected_and_output.split('\n'))
        self.assertEqual(report_parts(self.xor_gate, level=2).split('\n'),
                         expected_xor_output.split('\n'))


    def test_list_parts_3levels(self):
        expected_xor_output = """
Xor
  Not-1
    Nand-1-1
  Not-2
    Nand-2-1
  And-3
    Nand-3-1
    Not-3-2
      Nand-3-2-1
  And-4
    Nand-4-1
    Not-4-2
      Nand-4-2-1
  Or-5
    Not-5-1
      Nand-5-1-1
    Not-5-2
      Nand-5-2-1
    Nand-5-3
""".strip()
        
        self.assertEqual(report_parts(self.xor_gate, level=3).split('\n'),
                         expected_xor_output.split('\n'))


class TestInternalComponents(unittest.TestCase):
    def setUp(self):
        self.not_gate = Not()
        self.and_gate = And()
        self.xor_gate = Xor()

    def test_get_internal_components(self):
        self.assertEqual(self.not_gate['Nand-1'],
                         self.not_gate.internal_components[0])

        self.assertEqual(self.xor_gate['Nand-5-2-1'],
                         self.xor_gate.internal_components[4]
                         .internal_components[1]
                         .internal_components[0])

class TestTracing(unittest.TestCase):
    def setUp(self):
        self.not_gate = Not()
        self.and_gate = And()
        self.xor_gate = Xor()

    def test_not_trace(self):
        self.assertEqual(trace(self.not_gate, {'In':'0011',}, ['out']),
                         {'out':'1100'})

    def test_and_trace(self):
        self.assertEqual(trace(self.and_gate, {'a':'0011', 'b':'0101',}, ['out']),
                         {'out':'0001'})

    def test_and_trace_level2(self):
        self.assertEqual(trace(self.and_gate,
                               {'a':'0011', 'b':'0101',},
                               ['And:out', 'Nand-1:out', 'Not-2:In', 'Not-2:out', 'Nand-2-1:a'],
                               level=2),
                         {'And:out':'0001',
                          'Nand-1:out':'1110',
                          'Not-2:In':'1110',
                          'Not-2:out':'0001',
                          'Nand-2-1:a':'1110'})

    def test_xor_trace(self):
        self.assertEqual(trace(self.xor_gate, {'a':'0011', 'b':'0101'}, ['out']),
                         {'out':'0110'})

    def test_xor_trace_level2(self):
        self.assertEqual(trace(self.xor_gate,
                               {'a':'0011', 'b':'0101'},
                               ['Xor:out', 'Or-5:a', 'Or-5:b', 'Not-5-1:In', 'Not-5-1:out'],
                               level=2),
                         {'Xor:out': '0110',
                          'Or-5:a': '0010',
                          'Or-5:b': '0100',
                          'Not-5-1:In': '0010',
                          'Not-5-1:out': '1101'})


class Inc2(Component):
    IN = [w(2).In]
    OUT = [w(2).out]

    PARTS = [
        FullAdder(a=w.In[0], b=w.one, carry_in=w.zero, s=w.out[0], carry_out=w.carry0),
        FullAdder(a=w.In[1], b=w.zero, carry_in=w.carry0, s=w.out[1], carry_out=w.carry1),
    ]

class Counter2(Component):
    IN = []
    OUT = [w(2).out]

    PARTS = [
        DFF(In=w(2).updated_counter[0], out=w.out[0]),
        DFF(In=w(2).updated_counter[1], out=w.out[1]),
        Inc2(In=w.out, out=w.updated_counter)
    ]

class TestTracingEmptyInput(unittest.TestCase):
    def setUp(self):
        self.counter2 = Counter2()

    def test_empty(self):
        output = trace(self.counter2, {}, ['out'], step=20)


if __name__ == '__main__':
    unittest.main()

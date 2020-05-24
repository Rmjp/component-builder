import unittest

from compbuilder import Signal
from test.basic_gates import Nand, Not, And, Or, Xor, HalfAdder, FullAdder

T = Signal.T
F = Signal.F

from compbuilder.tracing import report_parts

class TestListParts(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()

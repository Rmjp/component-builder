import unittest

from compbuilder.n2t.asm import assemble

ADD100_ASM = """
// Adds 1+...+100.
	@i
	M=1
	@sum
	M=0
(LOOP)
	@i
	D=M	// D=i
	@100
	D=D-A	// D=i-100
	@END
	D;JGT	// If (i-100)>0 goto END
	@i
	D=M
	@sum
	M=D+M
	@i
	M=M+1
	@LOOP
	0;JMP
(END)
	@END
	0;JMP
"""

EXPECTED_ADD100_INSTRUCTIONS = [
    0b0000000000010000,
    0b1110111111001000,
    0b0000000000010001,
    0b1110101010001000,
    0b0000000000010000,
    0b1111110000010000,
    0b0000000001100100,
    0b1110010011010000,
    0b0000000000010010,
    0b1110001100000001,
    0b0000000000010000,
    0b1111110000010000,
    0b0000000000010001,
    0b1111000010001000,
    0b0000000000010000,
    0b1111110111001000,
    0b0000000000000100,
    0b1110101010000111,
    0b0000000000010010,
    0b1110101010000111,
]

class TestAssembler(unittest.TestCase):

    def test_add100_asm(self):
        instructions = assemble(ADD100_ASM)
        self.assertEqual(instructions, EXPECTED_ADD100_INSTRUCTIONS)

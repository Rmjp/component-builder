from compbuilder import Signal

def trim16bit(x):
    return x & 0xffff

def trim15bit(x):
    return x & 0x7fff

def neg_bits(x):
    return 0xffff - trim16bit(x)

def two_compliment(x):
    return trim16bit(neg_bits(x) + 1)

MINUS_ONE = 0xffff

FUNC_MAP = {
    0b101010: lambda opr1, opr2: 0,
    0b111111: lambda opr1, opr2: 1,
    0b111010: lambda opr1, opr2: MINUS_ONE,
    0b001100: lambda opr1, opr2: opr1,
    0b110000: lambda opr1, opr2: opr2,

    0b001101: lambda opr1, opr2: neg_bits(opr1),
    0b110001: lambda opr1, opr2: neg_bits(opr2),
    
    0b001111: lambda opr1, opr2: two_compliment(opr1),
    0b110011: lambda opr1, opr2: two_compliment(opr2),
    
    0b011111: lambda opr1, opr2: trim16bit(opr1 + 1),
    0b110111: lambda opr1, opr2: trim16bit(opr2 + 1),
    
    0b001110: lambda opr1, opr2: trim16bit(opr1 + MINUS_ONE),
    0b110010: lambda opr1, opr2: trim16bit(opr2 + MINUS_ONE),
    
    0b000010: lambda opr1, opr2: trim16bit(opr1 + opr2),
    0b010011: lambda opr1, opr2: trim16bit(opr1 + two_compliment(opr2)),

    0b000111: lambda opr1, opr2: trim16bit(two_compliment(opr1) + opr2),

    0b000000: lambda opr1, opr2: opr1 & opr2,
    0b010101: lambda opr1, opr2: opr1 | opr2,
}

class PureHackCPU:
    """
    >>> c = PureHackCPU()
    >>> c.load_instructions([60048, 61392, 61072, 1234, 60432, 58192, 60496, 58320, 60624, 4411, 60880, 59344, 57488, 58576, 30000, 57808, 12, 60432, 10, 57360, 12, 60432, 10, 58704, 58128, 60432])
    >>> c.reset()
    >>> c.run(26)
    {'pc': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26], 'a': [0, 0, 0, 1234, 1234, 1234, 1234, 1234, 1234, 4411, 4411, 4411, 4411, 4411, 30000, 30000, 12, 12, 10, 10, 12, 12, 10, 10, 10, 10], 'd': [0, 1, 65535, 65535, 1234, 64301, 64301, 1235, 64302, 64302, 4412, 4413, 8824, 4413, 4413, 25587, 25587, 12, 12, 8, 8, 12, 12, 14, 14, 10]}
    """
    def __init__(self):
        self.a = 0
        self.d = 0
        self.pc = 0
        self.ram = [0] * 0x8000
        self.rom = [0] * 0x8000
        self.reset()

    def reset(self):
        self.pc = 0

    def load_instructions(self, insts):
        for i,addr in zip(insts, range(len(insts))):
            self.rom[addr] = i

    def is_a_instruction(self, inst):
        return (inst & 0x8000) == 0

    def decode(self, inst):
        a = (inst >> 12) & 1
        c = (inst >> 6) & 63
        d = (inst >> 3) & 7
        j = inst & 7
        return a,c,d,j

    def inc_pc(self):
        self.pc = trim15bit(self.pc + 1)

    def store_result(self, dest, result):
        if (dest & 0b001) > 0:
            self.ram[this.a] = result

        if (dest & 0b010) > 0:
            self.d = result

        if (dest & 0b100) > 0:
            self.a = result

    def jump(self, jmp, result, location):
        zero = result == 0
        neg = (result & 0x8000) > 0
        pos = (not neg) and (not zero)

        if ((((jmp & 0b100) > 0) and (neg)) or
            (((jmp & 0b010) > 0) and (zero)) or
            (((jmp & 0b001) > 0) and (pos))):
            self.pc = location
        else:
            self.inc_pc()
            
    def step(self):
        inst = self.rom[self.pc]

        if self.is_a_instruction(inst):
            self.a = inst
            self.inc_pc()
        else:
            a,c,d,j = self.decode(inst)

            if a == 0:
                op2 = self.a
            else:
                op2 = self.ram[trim15bit(self.a)]

            org_jump_location = self.a
            
            result = FUNC_MAP[c](self.d, op2)
            result = trim16bit(result)

            self.store_result(d, result)
            self.jump(j, result, org_jump_location)
    
    def run(self, num_step):
        traces = {
            'pc':[],
            'a':[],
            'd':[]
        }
        for i in range(num_step):
            self.step()
            traces['pc'].append(self.pc)
            traces['a'].append(self.a)
            traces['d'].append(self.d)

        return traces
        

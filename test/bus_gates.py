from compbuilder import Component, Signal
from compbuilder import w

from .basic_gates import Nand

class And2(Component):
    IN = [w(2).a, w(2).b]
    OUT = [w(2).out]

    PARTS = [
    ]

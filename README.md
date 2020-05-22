## Component Builder

This library provides DSL for constructing and testing digital circuit components with HDL-like interface.

### Examples

Describe inputs and outputs with `IN` and `OUT` lists.  Put component parts in `PARTS`.

#### NOT gate and AND gate implementations from NAND gates

```python
class Not(Component):
    IN = [w.a]
    OUT = [w.out]
    PARTS = [
        Nand(a=w.a, b=w.a, out=w.out),
    ]

class And(Component):
    IN = [w.a, w.b]
    OUT = [w.out]
    PARTS = [
        Nand(a=w.a, b=w.b, out=w.c),
        Not(a=w.c, out=w.out),
    ]
```

#### Use your own implementations for basic gates
```python
class Nand(Component):
    IN = [w.a, w.b]
    OUT = [w.out]

    PARTS = []

    def process(self, a, b):
        if (a.get()==1) and (b.get()==1):
            return Signal(0)
        else:
            return Signal(1)
```

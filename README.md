## Component Builder

This library provides DSL for constructing and testing digital circuit components with HDL-like interface.

### Examples

Describe inputs and outputs with `IN` and `OUT` lists.  Put component parts in `PARTS`.  More examples in the test directory.

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

#### Specify signal bus size with `w()` and use slices

```python
class And2(Component):
    IN = [w(2).a, w(2).b]
    OUT = [w(2).out]

    PARTS = [
        And(a=w(2).a[0], b=w(2).b[0],
             out=w(2).out[0]),
        And(a=w(2).a[1], b=w(2).b[1],
             out=w(2).out[1]),
    ]
```

#### Dynamically specify parts using Python codes

```python
class And8(Component):
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
```

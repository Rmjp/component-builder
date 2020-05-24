class Signal:
    """
    >>> s = Signal(26,6)
    >>> str(s)
    '011010'

    >>> str(s.slice(slice(1,2)))
    '1'
    >>> str(s.slice(slice(0,2)))
    '10'
    >>> str(s.slice(slice(1,5)))
    '1101'
    >>> str(s.slice(slice(2,6)))
    '0110'
    >>> s.set_slice(slice(2,6), Signal(8,4))
    >>> str(s)
    '100010'
    >>> s = Signal(26,6); s.set_slice(slice(2,3), Signal(1,1))
    >>> str(s)
    '011110'
    >>> s = Signal(26,6); s.set_slice(slice(0,4), Signal(3,4))
    >>> str(s)
    '010011'
    """
    def __init__(self, value, width=1):
        self.value = value
        self.width = width

    def get(self):
        return self.value

    def resize(self, new_width):
        return Signal(self.value, new_width)
    
    def __eq__(self, other):
        if other == None:
            return False
        return ((self.width == other.width) and
                (self.value == other.value))

    def __str__(self):
        fmt = '{:0%db}' % (self.width,)
        return fmt.format(self.value)

    @staticmethod
    def from_string(s):
        return Signal(int(s,2), len(s))
    
    def slice(self, s):
        rev = str(self)[::-1]
        return Signal.from_string((rev[s])[::-1])

    def set_slice(self, s, value):
        slen = s.stop - s.start
        fmt = '{:0%db}' % (slen)
        vstr = fmt.format(value.value)
        rev_str = list(str(self)[::-1])
        rev_str[s] = list(vstr[::-1])
        self.value = int(''.join(rev_str[::-1]),2)

    def __getitem__(self,key):
        if type(key) == slice:
            return self.slice(key)
        else:
            return self.slice(slice(key,key+1))

Signal.F = Signal(0)
Signal.T = Signal(1)
    
class Component:
    class Node:
        def __init__(self, id, component):
            self.id = id
            self.component = component
            self.in_dict = {}
            self.out_dict = {}
            self.in_wires = {}
            self.out_wires = {}
            self.in_list = []
            self.out_list = []
            self.indegree = 0
            self.outdegree = 0

    def init_parts(self):
        pass
            
    def __init__(self, **kwargs):
        self.init_parts()

        self.component_name = ''
        self.internal_components = None
        self.wire_assignments = kwargs
        self.graph = None
        self.is_initialized = False

    def shallow_clone(self):
        return type(self)(**self.wire_assignments)

    def get_or_create_edge(self, estr):
        if estr in self.edges:
            e = self.edges[estr]
        else:
            e = {
                'src': [],
                'dest': [],
                'value': None,
            }
            self.edges[estr] = e
        return e

    def top_sort(self):
        self.topo_ordering = []

        for uid in self.nodes:
            u = self.nodes[uid]
            u.current_indegree = u.indegree

        for wire in self.IN:
            e = self.edges[wire.get_key()]
            for vid in e['dest']:
                self.nodes[vid].current_indegree -= 1
                    
        src_list = []
        for uid in self.nodes:
            u = self.nodes[uid]
            if u.current_indegree == 0:
                src_list.append(u)

        ncount = 0
        while len(src_list)!=0:
            ncount += 1
            u = src_list[0]
            src_list = src_list[1:]

            self.topo_ordering.append(u)
            for e in u.out_list:
                for vid in e['dest']:
                    v = self.nodes[vid]
                    v.current_indegree -= 1
                    if v.current_indegree == 0:
                        src_list.append(v)

        if ncount != self.n:
            raise Exception('Loop in component parts found')
    
    def build_graph(self):
        if not getattr(self, 'PARTS', None):
            self.PARTS = []
        
        self.nodes = {}
        self.edges = {}
        self.internal_components = []
        self.n = len(self.PARTS)

        ncount = 0
        for p in self.PARTS:
            ncount += 1
            nid = ncount

            p.validate_config()
            component = p.shallow_clone()
            component.build_graph()
            
            self.internal_components.append(component)

            node = self.Node(nid, component)

            self.nodes[nid] = node

            for wire in component.IN:
                key = wire.get_key()
                actual_wire = component.get_actual_edge(wire.name)
                actual_key = actual_wire.get_key()
                node.in_dict[key] = actual_key
                node.in_wires[key] = actual_wire

                e = self.get_or_create_edge(actual_key)
                e['dest'].append(nid)
                node.in_list.append(e)
                
            for wire in component.OUT:
                key = wire.get_key()
                actual_wire = component.get_actual_edge(wire.name)
                actual_key = actual_wire.get_key()
                node.out_dict[key] = actual_key
                node.out_wires[key] = actual_wire
                
                e = self.get_or_create_edge(actual_key)
                e['src'].append(nid)
                node.out_list.append(e)

        for estr in self.edges:
            e = self.edges[estr]

            for nid in e['dest']:
                u = self.nodes[nid]
                if e['src'] != []:
                    u.indegree += len(e['src'])
                else:
                    u.indegree += 1
                
            for nid in e['src']:
                u = self.nodes[nid]
                u.outdegree += len(e['dest'])

        if self.PARTS:
            self.top_sort()

        self.graph = {
            'nodes': self.nodes,
            'edges': self.edges,
        }

    def get_actual_edge(self, estr):
        return self.wire_assignments[estr]
        
    def validate_config(self):
        for wire in self.IN + self.OUT:
            name = wire.name
            if name not in self.wire_assignments:
                raise Exception('Incomplete wire configuration: ' + name)

    def initialize(self):
        if self.is_initialized:
            return

        self.build_graph()
        
        self.is_initialized = True
            
    def process(self, **kwargs):
        self.initialize()
        
        for wire in self.IN:
            key = wire.get_key()
            self.edges[key]['value'] = kwargs[wire.name]

        input_kwargs = {}
        for u in self.topo_ordering:
            for k in u.in_dict:
                wire = u.in_wires[k]
                input_kwargs[k[0]] = wire.slice_signal(self.edges[u.in_dict[k]]['value'])
            output = u.component.process(**input_kwargs)
            for k,v in zip(u.component.OUT, output):
                estr = k.get_key()
                wire = u.out_wires[estr]
                self.edges[u.out_dict[estr]]['value'] = wire.save_to_signal(self.edges[u.out_dict[estr]]['value'],v)

        return [self.edges[wire.get_key()]['value'] for wire in self.OUT]

    def eval(self, **kwargs):
        return self.process(**kwargs)
    
    def eval_single(self, **kwargs):
        return self.process(**kwargs)[0]

    def get_gate_name(self):
        return self.__class__.__name__

    
class Wire:
    def __init__(self, name, width=1, slice=None):
        self.name = name
        self.width = width
        self.slice = slice
        
    def get_key(self):
        return (self.name, self.width)

    def __getitem__(self, key):
        if type(key) == slice:
            return Wire(self.name, self.width, key)
        else:
            return Wire(self.name, self.width, slice(key,key+1))

    def slice_signal(self, signal):
        if self.slice:
            return signal.slice(self.slice)
        else:
            return signal

    def save_to_signal(self, signal, value):
        if self.slice:
            if signal == None:
                signal = Signal(0, self.width)
            signal.set_slice(self.slice, value)
            return signal
        else:
            return value
    
class WireFactory:
    __instances = None
    
    @staticmethod
    def get_instance(width=1):
        if WireFactory.__instances == None:
            WireFactory()

        if width not in WireFactory.__instances:
            WireFactory.__instances[width] = WireFactory(width)

        return WireFactory.__instances[width]

    def __call__(self, width):
        return WireFactory.get_instance(width)
    
    def __getattr__(self, name):
        return Wire(name, self.width)
    
    def __init__(self, width=1):
        if (WireFactory.__instances != None) and (width in WireFactory.__instances):
            raise Exception('You should not try to instatiate WireFactory directly')

        self.width = width

        if WireFactory.__instances == None:
            WireFactory.__instances = {}

        WireFactory.__instances[width] = self
        
w = WireFactory.get_instance()


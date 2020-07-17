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
        if type(other) == int:
            return self.value == other
        else:
            return ((self.width == other.width) and
                    (self.value == other.value))

    def __str__(self):
        fmt = '{:0%db}' % (self.width,)
        return fmt.format(self.value)

    def __repr__(self):
        return str(self)

    def __format__(self, format_spec):
        if format_spec[-1] != 'X':
            return self.value.__format__(format_spec)
        else:
            return '{:X}'.format(self.value)
    
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
            self.is_deferred = False

    def init_parts(self):
        pass
            
    def __init__(self, **kwargs):
        self.init_parts()

        self.component_name = ''
        self.internal_components = None
        self.wire_assignments = kwargs
        self.graph = None
        self.is_initialized = False

        self.preprocessing_hooks = {}
        self.postprocessing_hooks = {}

        self.is_clocked_component = False
        self.clocked_components = []
        self.saved_input_kwargs = None
        

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

    def normalize_component_wire_widths(self):
        def normalize_wire_width(wire, widths):
            if wire.name in widths:
                return Wire(wire.name, widths[wire.name], wire.slice, wire.constant_value)
            else:
                return wire
        
        widths = {}
        all_wires = self.IN + self.OUT
        for component in self.PARTS:
            for wire in component.IN + component.OUT:
                key = wire.get_key()
                actual_wire = component.get_actual_wire(wire.name)
                all_wires.append(actual_wire)
            
        for w in all_wires:
            if (w.name not in widths) or (widths[w.name] == 1):
                widths[w.name] = w.width
            elif (w.width != 1) and (widths[w.name] != w.width):
                raise Exception('Wire width mismatch {} and {}'.format(widths[w.name],w.width))

        self.IN = [normalize_wire_width(w, widths) for w in self.IN]
        self.OUT = [normalize_wire_width(w, widths) for w in self.OUT]
        for component in self.PARTS:
            for wire in component.IN + component.OUT:
                actual_wire = component.get_actual_wire(wire.name)
                component.set_actual_wire(wire.name, normalize_wire_width(actual_wire, widths))
                new_actual_wire = component.get_actual_wire(wire.name)

                
    def top_sort(self):
        self.topo_ordering = []

        for uid in self.nodes:
            u = self.nodes[uid]
            u.current_indegree = u.indegree
            for w in u.in_wires.values():
                if w.is_constant:
                    u.current_indegree -= 1

        for wire in self.IN:
            e = self.edges[wire.get_key()]
            for vid in e['dest']:
                self.nodes[vid].current_indegree -= 1
                    
        src_list = []
        added_set = set()
        for uid in self.nodes:
            u = self.nodes[uid]
            if (u.current_indegree == 0) or (u.component.is_clocked_component):
                src_list.append(u)
                added_set.add(u.id)

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
                        if v.id not in added_set:
                            src_list.append(v)
                            added_set.add(v.id)

        if ncount != self.n:
            raise Exception('Loop in component parts found')

        self.topo_ordering = [u for u in self.topo_ordering if not u.component.is_clocked_component]
        
        for uid in self.nodes:
            u = self.nodes[uid]
            if u.component.is_clocked_component:
                u.is_deferred = True
                self.topo_ordering.append(u)

    
    def add_wire_to_node_in_edge(self, node, wire, component):
        key = wire.get_key()
        actual_wire = component.get_actual_wire(wire.name)
        actual_key = actual_wire.get_key()
        node.in_dict[key] = actual_key
        node.in_wires[key] = actual_wire

        e = self.get_or_create_edge(actual_key)
        e['dest'].append(node.id)
        node.in_list.append(e)
                
    def add_wire_to_node_out_edge(self, node, wire, component):
        key = wire.get_key()
        actual_wire = component.get_actual_wire(wire.name)
        actual_key = actual_wire.get_key()
        node.out_dict[key] = actual_key
        node.out_wires[key] = actual_wire
                
        e = self.get_or_create_edge(actual_key)
        e['src'].append(node.id)
        node.out_list.append(e)

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
            component.initialize()
            if component.is_clocked_component:
                self.is_clocked_component = True
                self.clocked_components.append(component)
            
            self.internal_components.append(component)

            node = self.Node(nid, component)
            component.node = node

            self.nodes[nid] = node

            for wire in component.IN:
                self.add_wire_to_node_in_edge(node, wire, component)
                
            for wire in component.OUT:
                self.add_wire_to_node_out_edge(node, wire, component)

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

        """
        print()
        print('--- graph ---', self)
        print(self, 'NODES:', self.nodes)
        for uid in self.nodes:
            u = self.nodes[uid]
            print(' - ', uid, u.component)
            print('   ', u.in_dict, u.in_wires)
        print(self, 'EDGES:', self.edges)
        print()
        """
        
    def get_actual_wire(self, estr):
        return self.wire_assignments[estr]

    def set_actual_wire(self, estr, wire):
        self.wire_assignments[estr] = wire    
        
    def validate_config(self):
        for wire in self.IN + self.OUT:
            name = wire.name
            if name not in self.wire_assignments:
                raise Exception('Incomplete wire configuration: ' + name)

    def initialize(self):
        if self.is_initialized:
            return

        self.normalize_component_wire_widths()
        self.build_graph()
        
        self.set_constants()
            
        self.is_initialized = True

    def propagate_output(self, u, output):
        for w in u.component.OUT:
            v = output[w.name]
            estr = w.get_key()
            wire = u.out_wires[estr]
            self.edges[u.out_dict[estr]]['value'] = wire.save_to_signal(self.edges[u.out_dict[estr]]['value'],v)

    def set_constants(self):
        #if self.get_gate_name() == 'AutoCounter':
        #    print('=================={}==================='.format(self.get_gate_name()))
        #    print(self.edges)
        for uid in self.nodes:
            u = self.nodes[uid]
            for w in u.in_wires.values():
                if w.is_constant:
                    estr = w.get_key()
                    self.edges[estr]['value'] = w.get_constant_signal()
            
    def process(self, **kwargs):
        self.initialize()

        self.saved_input_kwargs = kwargs
        
        for wire in self.IN:
            key = wire.get_key()
            self.edges[key]['value'] = kwargs[wire.name]

        for u in self.topo_ordering:
            input_kwargs = {}
            for k in u.in_dict:
                wire = u.in_wires[k]
                input_kwargs[k[0]] = wire.slice_signal(self.edges[u.in_dict[k]]['value'])

            #print("IN:", u.component, u.in_dict, input_kwargs)
            output = u.component._process(**input_kwargs)
            if not u.is_deferred:
                self.propagate_output(u, output)
            
        return {wire.name:self.edges[wire.get_key()]['value'] for wire in self.OUT}

    def process_deffered(self):
        self.initialize()

        if not self.is_clocked_component:
            return {}
        
        kwargs = self.saved_input_kwargs
        
        for wire in self.IN:
            key = wire.get_key()
            if kwargs != None:
                self.edges[key]['value'] = kwargs[wire.name]

        node_ordering = [u for u in self.topo_ordering if u.is_deferred == True]

        for u in node_ordering:
            output = u.component._process_deffered()
            self.propagate_output(u, output)

        return {wire.name:self.edges[wire.get_key()]['value'] for wire in self.OUT}
    
    def _process(self, **kwargs):
        for f in self.preprocessing_hooks.values():
            f(self, kwargs)

        #print(">>", self, kwargs)
        output = self.process(**kwargs)

        for f in self.postprocessing_hooks.values():
            f(self, kwargs, output)

        self.trace_input_signals = kwargs
        self.trace_output_signals = output
        self.trace_signals = {**kwargs, **self.trace_output_signals}
            
        return output
    
    def _process_deffered(self):
        kwargs = self.saved_input_kwargs
        if kwargs == None:
            kwargs = {}
        for f in self.preprocessing_hooks.values():
            f(self, kwargs)

        #print(">>", self, kwargs)
        output = self.process_deffered()

        for f in self.postprocessing_hooks.values():
            f(self, kwargs, output)

        self.trace_input_signals = kwargs
        self.trace_output_signals = output
        self.trace_signals = {**kwargs, **self.trace_output_signals}
            
        return output
    
    def eval(self, **kwargs):
        #if self.is_clocked_component:
        self._process_deffered()
        return self._process(**kwargs)
    
    def eval_single(self, **kwargs):
        output = self.eval(**kwargs)
        if len(output.keys()) != 1:
            raise Exception("eval single works only with output with exactly one wire")
        return list(output.values())[0]

    def get_gate_name(self):
        return self.__class__.__name__

    def add_preprocessing_hook(self, key, f):
        self.preprocessing_hooks[key] = f
    
    def add_postprocessing_hook(self, key, f):
        self.postprocessing_hooks[key] = f
    
    def __getitem__(self, key):
        self.initialize()
        index_items = key.split('-')
        if len(index_items) <= 1:
            if self.get_gate_name() == key:
                return self
            raise Exception('Internal component access error with key: ' + key)

        try:
            indices = [int(x) for x in index_items[1:]]
        except:
            raise Exception('Internal component access error with key: ' + key)

        component = self
        for i in indices:
            component = component.internal_components[i-1]

        if component.get_gate_name() != index_items[0]:
            raise Exception('Internal component access error gate type mismatch: ' + key + ' with ' + component.get_gate_name())

        return component
    
    
class Wire:
    def __init__(self, name, width=1, slice=None, constant_value=None):
        self.name = name
        self.width = width
        self.slice = slice
        if constant_value != None:
            self.is_constant = True
            self.constant_value = constant_value
        else:
            self.is_constant = False
            self.constant_value = None
        
    def __str__(self):
        return '{}:{}'.format(self.name, self.width)

    def get_key(self):
        return (self.name, self.width)

    def __getitem__(self, key):
        if type(key) == slice:
            return Wire(self.name, self.width, key, self.constant_value)
        else:
            return Wire(self.name, self.width, slice(key,key+1), self.constant_value)

    def slice_signal(self, signal):
        if self.slice:
            return signal.slice(self.slice)
        else:
            return signal

    def get_constant_signal(self):
        if not self.is_constant:
            raise Exception('A non-constant wire does not have constant_value')
        if self.slice:
            signal = Signal(0, self.width)
            signal.set_slice(self.slice, self.constant_value)
            return signal
        else:
            return Signal(self.constant_value, self.width)
        
    def save_to_signal(self, signal, value_signal):
        if self.is_constant:
            raise Exception('Cannot save to constant wires')
        if self.slice:
            if signal == None:
                signal = Signal(0, self.width)
            signal.set_slice(self.slice, value_signal)
            return signal
        else:
            return value_signal
    
class WireFactory:
    __instances = None

    CONSTANT_FUNCTIONS = {
        'T': lambda width: 1,
        'F': lambda width: 0,
        'one': lambda width: (1 << width) - 1,
        'zero': lambda width: 0,
    }
    
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
        if name in WireFactory.CONSTANT_FUNCTIONS:
            value = WireFactory.CONSTANT_FUNCTIONS[name](self.width)
            return Wire('__constant__{}_w{}_{}'.format(name, self.width, value), self.width, constant_value=value)
        else:
            return Wire(name, self.width)
    
    def __init__(self, width=1):
        if (WireFactory.__instances != None) and (width in WireFactory.__instances):
            raise Exception('You should not try to instatiate WireFactory directly')

        self.width = width

        if WireFactory.__instances == None:
            WireFactory.__instances = {}

        WireFactory.__instances[width] = self
        
w = WireFactory.get_instance()


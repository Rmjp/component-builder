from .exceptions import ComponentError, WireError

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

class SimulationMixin:
    class SimNode:
        def __init__(self, id, component):
            self.id = id
            self.component = component
            self.in_keys = component.get_in_keys()
            self.out_keys = component.get_out_keys()
            self.in_mapped_wires = [component.wire_map[k][0] for k in component.get_in_keys()]
            self.out_mapped_wires = [component.wire_map[k][0] for k in component.get_out_keys()]
            self.in_edge_keys = []
            self.out_edge_keys = []
            self.indegree = 0
            self.outdegree = 0
            self.is_pair_node = False
            self.is_input_node = False
            self.is_output_node = False

        def get_top_level_components(self, depth=1):
            c = self.component
            parents = []
            while c.parent_component != None:
                parents.append(c)
                c = c.parent_component
            parents.reverse()
            return parents[:depth]

    def extract_nets(self):
        self.initialize()
        
        base_components = []
        all_components = []
        ccount = [0]
        
        def assign_component_cid(component):
            ccount[0] += 1
            component.cid = ccount[0]

            for c in component.internal_components:
                c.parent_component = component
                assign_component_cid(c)
        
        def extract_base_components(component):
            all_components.append(component)
            if component.internal_components == []:
                base_components.append(component)
            else:
                for c in component.internal_components:
                    extract_base_components(c)

        assign_component_cid(self)
        extract_base_components(self)
        return (base_components, all_components)

    def trace_wire(self):
        #print('Trace', self.cid, self)
        wire_map = {}
        terminated = {}
        for k in self.get_in_keys() + self.get_out_keys():
            wire_map[k] = [{'cid':self.cid,
                            'key':k,
                            'component_width': k[1],
                            'offset':0,
                            'is_constant': False,
                            'actual_wire': None}]
            terminated[k] = False
            
        component = self
        while component.parent_component:
            in_out_keys = component.parent_component.get_in_keys() + component.parent_component.get_out_keys()
            #print('IN OUT:', component, in_out_keys)
            for w in wire_map:
                if not terminated[w]:
                    cw = wire_map[w][0]['key']
                    #print('current', cw, component)
                    if cw[0] in component.wire_assignments:
                        new_w = component.wire_assignments[cw[0]]
                        new_key = new_w.get_key()
                        new_offset = wire_map[w][0]['offset']
                        if new_w.slice:
                            new_offset += new_w.slice.start
                    else:
                        raise Exception('wire disappeared')
                    #print('in', component, wire_map[w], new_w, new_key)
                    #print('new', cw, component.parent_component.cid, new_key) 
                    wire_map[w].insert(0,{'cid':component.parent_component.cid,
                                          'key':new_key,
                                          'component_width':wire_map[w][0]['component_width'],
                                          'offset': new_offset,
                                          'is_constant': new_w.is_constant,
                                          'actual_wire': new_w})
                    if new_key not in in_out_keys:
                        terminated[w] = True
                        #print('Final', w, wire_map[w][0])
            component = component.parent_component

        return wire_map

    def sum_wire_width(self, wires):
        return sum([w.width for w in wires])
    
    def build_sim_graph(self):
        base_components, all_components = self.extract_nets()

        self.sim_base_components = base_components
        self.sim_all_components = all_components
        
        nodes = {}
        self.sim_edges = {}

        def get_or_create_edge(edge_key):
            if edge_key in self.sim_edges:
                return self.sim_edges[edge_key]
            else:
                e = {
                    'src': [],
                    'dest': [],
                    'signal': None
                }
                self.sim_edges[edge_key] = e
                return e

        ncount = 0

        for c in all_components:
            c.wire_map = c.trace_wire()
        
        for c in base_components:
            if c.is_clocked_component:
                ncount += 1
                in_node = self.SimNode(ncount, c)
                in_node.is_pair_node = True
                in_node.is_input_node = True
                nodes[in_node.id] = in_node
                
                ncount += 1
                out_node = self.SimNode(ncount, c)
                out_node.is_pair_node = True
                out_node.is_output_node = True
                nodes[out_node.id] = out_node

                ek = (c.cid, ('in-out-pair',1))
                e = get_or_create_edge(ek)
                e['src'].append(out_node.id)
                e['dest'].append((in_node.id, 1))

                in_node.in_edge_keys.append(ek)
                out_node.out_edge_keys.append(ek)

                in_node.indegree = self.sum_wire_width(c.IN) + 1
                out_node.outdegree = self.sum_wire_width(c.OUT) + 1
            else:
                ncount += 1
                node = self.SimNode(ncount, c)
                nodes[node.id] = node
                node.indegree = self.sum_wire_width(c.IN)
                node.outdegree = self.sum_wire_width(c.OUT)

                in_node = node
                out_node = node

            for k in c.get_in_keys():
                wmap = c.wire_map[k][0]
                ek = (wmap['cid'], wmap['key'])
                e = get_or_create_edge(ek)
                e['dest'].append((in_node.id, wmap['component_width']))
                in_node.in_edge_keys.append(ek)

            for k in c.get_out_keys():
                wmap = c.wire_map[k][0]
                ek = (wmap['cid'], wmap['key'])
                e = get_or_create_edge(ek)
                e['src'].append(out_node.id)
                out_node.out_edge_keys.append(ek)

        self.sim_nodes = nodes
        self.sim_n = len(nodes)
        
        self.sim_graph = {
            'nodes': self.sim_nodes,
            'edges': self.sim_edges,
        }


    def check_loop(self):
        def dfs(u):
            u.is_visisted = True

            for ek in u.out_edge_keys:
                e = self.sim_edges[ek]
                for vid, edge_wire_width in e['dest']:
                    v = self.sim_nodes[vid]
                    if v.is_visisted:
                        if not v.is_returned:
                            # LOOP!
                            messages = ['Loop found:']
                            loop_components = [(u, u.component, u.parent_edge_key)]
                            current = u
                            while current != v:
                                current = current.dfs_parent
                                loop_components.append((current, current.component, current.parent_edge_key))

                            loop_components.reverse()
                            messages = ['Loop found:']
                            for u, c, ek in loop_components:
                                if not u.is_pair_node:
                                    messages.append(f' - {c} inside {u.get_top_level_components(self.sim_loop_report_levels)} - {ek}')
                                else:
                                    if u.is_input_node:
                                        messages.append(f' - {c} [IN] inside {u.get_top_level_components(self.sim_loop_report_levels)} - {ek}')
                                    else:
                                        messages.append(f' - {c} [OUT] inside {u.get_top_level_components(self.sim_loop_report_levels)} - {ek}')
                                        
                            raise ComponentError(message='\n'.join(messages))
                    else:
                        v.dfs_parent = u
                        v.parent_edge_key = ek
                        dfs(v)
            
            u.is_returned = True

        for uid in self.sim_nodes:
            u = self.sim_nodes[uid]
            u.is_visisted = False
            u.is_returned = False

        for uid in self.sim_nodes:
            u = self.sim_nodes[uid]

            if not u.is_visisted:
                u.dfs_parent = None
                u.parent_edge_key = None
                dfs(u)


    def top_sort(self):
        self.check_loop()
        
        self.sim_topo_ordering = []

        for uid in self.sim_nodes:
            u = self.sim_nodes[uid]
            u.current_indegree = u.indegree
            if u.is_output_node:
                continue
            for m_wire in u.in_mapped_wires:
                if m_wire['is_constant']:
                    u.current_indegree -= m_wire['component_width']

                    if u.current_indegree < 0:
                        raise ComponentError(messages=f'Implementation Error (negative indegree) {u.is_output_node} {u.current_indegree} {u.component} {m_wire}')

        for ek in self.sim_edges:
            e = self.sim_edges[ek]
            e['in_signals'] = len(e['src'])
            e['current_in_count'] = 0
                    
        for key in self.get_in_keys():
            try:
                e = self.sim_edges[(self.cid, key)]
            except KeyError as e:
                raise ComponentError(errors=e) from e
            for vid, wire_width in e['dest']:
                self.sim_nodes[vid].current_indegree -= wire_width
                    
        src_list = []
        added_set = set()

        for uid in self.sim_nodes:
            u = self.sim_nodes[uid]
            if u.current_indegree == 0:
                src_list.append(u)
                added_set.add(u.id)
                
        ncount = 0
        while len(src_list)!=0:
            ncount += 1
            u = src_list[0]
            src_list = src_list[1:]

            #print('Added:', u.component, u.get_top_level_components(2))
            
            self.sim_topo_ordering.append(u)

            for ek in u.out_edge_keys:
                e = self.sim_edges[ek]
                e['current_in_count'] += 1
                if e['current_in_count'] == e['in_signals']:
                    for vid, edge_wire_width in e['dest']:
                        v = self.sim_nodes[vid]
                        v.current_indegree -= edge_wire_width
                        if v.current_indegree == 0:
                            if v.id not in added_set:
                                src_list.append(v)
                                added_set.add(v.id)
                        elif v.current_indegree < 0:
                            print('ERROR:', v, v.component, v.current_indegree, ek, v.out_edge_keys, v.out_mapped_wires)    

        if ncount != self.sim_n:
            messages = ['ERROR: cannot find evaluation order.  Some input wire is missing.',
                        'Remaining components:']

            parent_set = set()
            err_count = 0
            for uid in self.sim_nodes:
                u = self.sim_nodes[uid]
                if u.id not in added_set:
                    component_parents = tuple(u.get_top_level_components(self.sim_loop_report_levels))
                    if err_count < self.sim_loop_max_num_report_primitives:
                        if not u.is_pair_node:
                            messages.append(f'- {u.id}: {u.component} (wait: {u.current_indegree}) (inside {component_parents}) in-wires: {[w["key"] for w in u.in_mapped_wires]}')
                        else:
                            if u.is_input_node:
                                messages.append(f'- {u.id}: {u.component} [IN] (wait: {u.current_indegree}) (inside {component_parents}) in-wires: {[w["key"] for w in u.in_mapped_wires]}')
                            else:
                                messages.append(f'- {u.id}: {u.component} [OUT] (wait: {u.current_indegree}) (inside {component_parents}) in-wires: {[w["key"] for w in u.in_mapped_wires]}')
                                
                    elif err_count == self.sim_loop_max_num_report_primitives:
                        messages.append('.... too many ....')
                    err_count += 1
                    parent_set.add(component_parents)
                    
            if err_count > self.sim_loop_max_num_report_primitives:
                messages.append(f'(for {err_count} components)')

            messages.append('Components with errors:')
            for p in sorted([str(pp) for pp in parent_set]):
                messages.append(f'- {p}')

            messages.append('All top level components:')
            for c in self.internal_components:
                messages.append(f'- {c}')
            
            raise ComponentError(message='\n'.join(messages))

    def get_signal_from_mapped_wire(self, signal, component_wire, mapped_wire):
        offset = mapped_wire['offset']
        if signal != None:
            signal_value = signal.value
        elif mapped_wire['is_constant']:
            signal_value = mapped_wire['actual_wire'].constant_value
        else:
            raise ComponentError(message='Required input signal not found')
        v = (signal_value) >> offset
        mask = (1 << component_wire.width) - 1
        return Signal(v & mask, 1)

    def extract_component_trace(self, component):
        component.trace_input_signals = self.get_component_input(component)
        component.trace_output_signals = self.get_component_output(component)
        component.trace_signals = {**component.trace_input_signals, **component.trace_output_signals}
    
    def extract_all_component_trace(self):
        for c in self.sim_all_components + [self]:
            self.extract_all_component_trace(c)

    def get_component_wire_signal(self, component, wire):
        key = wire.get_key()
        mapped_wire = component.wire_map[key][0]
        edge_key = (mapped_wire['cid'], mapped_wire['key'])
        return self.get_signal_from_mapped_wire(self.edge_values.get(edge_key, None),
                                                wire,
                                                mapped_wire)
                
    def get_component_input(self, component):
        return {wire.name:self.get_component_wire_signal(component, wire)
                for wire in component.IN}
    
    def get_component_output(self, component):
        return {wire.name:self.get_component_wire_signal(component, wire)
                for wire in component.OUT}
    
    def set_component_output(self, component, output):
        for component_wire in component.OUT:
            key = component_wire.get_key()
            mapped_wire = component.wire_map[key][0]
            edge_key = (mapped_wire['cid'], mapped_wire['key'])
            if edge_key not in self.edge_values:
                self.edge_values[edge_key] = Signal(0, mapped_wire['key'][1])
            signal = self.edge_values[edge_key]
            signal.set_slice(slice(mapped_wire['offset'], mapped_wire['offset']+1),
                             output[component_wire.name])

    def init_simulator(self):
        if not getattr(self, 'sim_topo_ordering', None):
            self.build_sim_graph()
            self.top_sort()
        self.edge_values = {}

    def init_component_input_edge_value(self, kwargs):
        for wire in self.IN:
            key = wire.get_key()
            ek = (self.cid, key)
            self.edge_values[ek] = kwargs[wire.name]

    def simulate(self, **kwargs):
        self.init_simulator()
        self.init_component_input_edge_value(kwargs)
        
        for u in self.sim_topo_ordering:
            component = u.component
            if (not u.is_pair_node) or (u.is_input_node):
                input_kwargs = self.get_component_input(component)
            else:
                input_kwargs = {}

            if (not u.is_pair_node) or (u.is_output_node):
                output = component.process(**input_kwargs)
                self.set_component_output(component, output)
            else:
                component.prepare_process(**input_kwargs)

        try:
            return {wire.name:self.edge_values[(self.cid, wire.get_key())] for wire in self.OUT}
        except KeyError as e:
            raise ComponentError(errors=e) from e

class Component(SimulationMixin):
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
            self.is_pair_node = False
            self.is_input_node = False
            self.is_output_node = False

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

        self.parent_component = None

        self.is_clk_wire_added = False

        self.sim_loop_report_levels = 2
        self.sim_loop_max_num_report_primitives = 50

    def shallow_clone(self):
        return type(self)(**self.wire_assignments)

    def init_interact(self):
        self.initialize()
        self.add_clk_wire()
    
    def add_clk_wire(self):
        if self.is_clocked_component:
            if 'clk' not in [w.name for w in self.IN]:
                self.is_clk_wire_added = True
                self.IN.append(w.clk)

                self.wire_assignments['clk'] = w.clk

                for node in self.nodes.values():
                    if node.component.is_clocked_component:
                        node.in_wires['clk'] = w.clk

                for c in self.internal_components:
                    c.add_clk_wire()

    def restore_clk_wire(self):
        if self.is_clk_wire_added:
            self.IN = [w for w in self.IN if w.name != 'clk']

            del self.wire_assignments['clk']

            for node in self.nodes.values():
                if node.component.is_clocked_component:
                    del node.in_wires['clk']
            
            for c in self.internal_components:
                c.restore_clk_wire()

            self.is_clk_wire_added = False
    
    def get_in_keys(self):
        return [w.get_key() for w in self.IN]
    
    def get_out_keys(self):
        return [w.get_key() for w in self.OUT]
    
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
                try:
                    actual_wire = component.get_actual_wire(wire.name)
                except:
                    raise ComponentError(message=f'Error wire not found when normalizing wire width of component {component} inside {self}.')
                all_wires.append(actual_wire)
            
        for w in all_wires:
            if (w.name not in widths) or (widths[w.name] == 1):
                widths[w.name] = w.width
            elif (w.width != 1) and (widths[w.name] != w.width):
                raise ComponentError(message='Wire width mismatch {} and {}'.format(widths[w.name],w.width))

        self.IN = [normalize_wire_width(w, widths) for w in self.IN]
        self.OUT = [normalize_wire_width(w, widths) for w in self.OUT]
        for component in self.PARTS:
            for wire in component.IN + component.OUT:
                actual_wire = component.get_actual_wire(wire.name)
                component.set_actual_wire(wire.name, normalize_wire_width(actual_wire, widths))
                new_actual_wire = component.get_actual_wire(wire.name)

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
        self.clocked_n = 0
        
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
                self.clocked_n += 1
            
            self.internal_components.append(component)

            node = self.Node(nid, component)
            component.node = node
            component.parent_component = self

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

        #if self.PARTS:
        #    self.top_sort()

        self.graph = {
            'nodes': self.nodes,
            'edges': self.edges,
        }

    def get_actual_wire(self, estr):
        if estr in self.wire_assignments:
            return self.wire_assignments[estr]
        else:
            raise ComponentError(message=f'Actual wire with key {estr} missing in {self}')

    def set_actual_wire(self, estr, wire):
        self.wire_assignments[estr] = wire    
        
    def validate_config(self):
        for wire in self.IN + self.OUT:
            name = wire.name
            if name not in self.wire_assignments:
                raise ComponentError(message='Incomplete wire configuration: ' + name)

            if self.wire_assignments[name].get_actual_wire_width() != wire.width:
                raise ComponentError(message=f'Wire width mismatch in {name}: required {wire.width}, actual {self.wire_assignments[name].get_actual_wire_width()} at component {self}')

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
            print('propagate:', w.name, u.out_dict[estr], wire.name)

    def set_constants(self):
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

            output = u.component._process(**input_kwargs)
            self.propagate_output(u, output)

        try:
            return {wire.name:self.edges[wire.get_key()]['value'] for wire in self.OUT}
        except KeyError as e:
            raise ComponentError(errors=e) from e

    def process_deffered(self,**kwargs):
        self.initialize()

        if self.PARTS == []:
            return {}
        
        #if not self.is_clocked_component:
        #    return {}
        
        #kwargs = self.saved_input_kwargs

        print('process deferred >', self, kwargs)
        
        for wire in self.IN:
            key = wire.get_key()
            if kwargs != None:
                self.edges[key]['value'] = kwargs[wire.name]

        node_ordering = [u for u in self.topo_ordering if u.is_deferred == True]
        print(node_ordering)

        for u in node_ordering:
            input_kwargs = {}
            for k in u.in_dict:
                wire = u.in_wires[k]
                if self.edges[u.in_dict[k]]['value'] != None:
                    input_kwargs[k[0]] = wire.slice_signal(self.edges[u.in_dict[k]]['value'])
                else:
                    print('Not found', k)

            if u.component.is_clocked_component:
                print('calling deffered process', u.component, input_kwargs)
                output = u.component._process_deffered(**input_kwargs)
            else:
                print('calling standard process', u.component, input_kwargs)
                output = u.component._process(**input_kwargs)
            #if str(type(self)) == "<class 'test.test_ram.RAM64'>":
            print('-->', u.component, input_kwargs, output)
            
            self.propagate_output(u, output)

        try:
            return {wire.name:self.edges[wire.get_key()]['value'] for wire in self.OUT}
        except KeyError as e:
            raise ComponentError(errors=e) from e
    
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
    
    def _process_deffered(self, **kwargs):
        if kwargs == {}:
            kwargs = self.saved_input_kwargs
        if kwargs == None:
            kwargs = {}

        for f in self.preprocessing_hooks.values():
            f(self, kwargs)

        #print(">>", self, kwargs)
        output = self.process_deffered(**kwargs)

        for f in self.postprocessing_hooks.values():
            f(self, kwargs, output)

        self.trace_input_signals = kwargs
        self.trace_output_signals = output
        self.trace_signals = {**kwargs, **self.trace_output_signals}
            
        return output
    
    def eval(self, **kwargs):
        return self.simulate(**kwargs)
    
        self._process_deffered(**kwargs)
        print(self,'DEFFERED')
        return self._process(**kwargs)
    
    def eval_single(self, **kwargs):
        output = self.eval(**kwargs)
        if len(output.keys()) != 1:
            raise ComponentError(message="eval single works only with output with exactly one wire")
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
            raise ComponentError(message='Internal component access error with key: ' + key)

        try:
            indices = [int(x) for x in index_items[1:]]
        except:
            raise ComponentError(message='Internal component access error with key: ' + key)

        component = self
        for i in indices:
            component = component.internal_components[i-1]

        if component.get_gate_name() != index_items[0]:
            raise ComponentError(message='Internal component access error gate type mismatch: ' + key + ' with ' + component.get_gate_name())

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
        if self.slice:
            return '{}:{}[{}-{}]'.format(self.name, self.width, self.slice.start, self.slice.stop)
        else:
            return '{}:{}'.format(self.name, self.width)

    def __repr__(self):
        return self.__str__()
    
    def get_key(self):
        return (self.name, self.width)

    def __getitem__(self, key):
        if type(key) == slice:
            return Wire(self.name, self.width, key, self.constant_value)
        else:
            return Wire(self.name, self.width, slice(key,key+1), self.constant_value)

    def get_actual_wire_width(self):
        if not self.slice:
            return self.width
        else:
            start,stop,_ = self.slice.indices(self.width)
            return stop - start
        
    def slice_signal(self, signal):
        if self.slice:
            return signal.slice(self.slice)
        else:
            return signal

    def get_constant_signal(self):
        if not self.is_constant:
            raise WireError(message='A non-constant wire does not have constant_value')
        if self.slice:
            signal = Signal(0, self.width)
            signal.set_slice(self.slice, self.constant_value)
            return signal
        else:
            return Signal(self.constant_value, self.width)
        
    def save_to_signal(self, signal, value_signal):
        if self.is_constant:
            raise WireError(message='Cannot save to constant wires')
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
        'T': lambda width: (1 << width) - 1,
        'F': lambda width: 0,
        'one': lambda width: (1 << width) - 1,
        'zero': lambda width: 0,
        'int_one': lambda width: 1,
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
        elif name == 'constant':
            def wire_function(value):
                return Wire('__constant__constant_w{}_{}'.format(self.width, value), self.width, constant_value=value)
            return wire_function
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


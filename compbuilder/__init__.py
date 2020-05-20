class Signal:
    def __init__(self, value, width=1):
        self.value = value
        self.width = width

    def get(self):
        return self.value

    def resize(self, new_width):
        return Signal(self.value, new_width)
    
    def __eq__(self, other):
        return ((self.width == other.width) and
                (self.value == other.value))

Signal.F = Signal(0)
Signal.T = Signal(1)
    
class Component:
    class Node:
        def __init__(self, id, component):
            self.id = id
            self.component = component
            self.in_dict = {}
            self.out_dict = {}
            self.in_list = []
            self.out_list = []
            self.indegree = 0
            self.outdegree = 0

    def __init__(self, **kwargs):
        self.internal_components = None
        self.wire_assignments = kwargs
        self.graph = None

    def shallow_clone(self):
        return type(self)(**self.wire_assignments)

    def get_or_create_edge(self, estr):
        if estr in self.edges:
            e = self.edges[estr]
        else:
            e = {
                'src': None,
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

        for estr in self.IN:
            e = self.edges[estr]
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
        self.nodes = {}
        self.edges = {}
        self.n = len(self.PARTS)
        
        ncount = 0
        for p in self.PARTS:
            ncount += 1
            nid = ncount

            p.validate_config()
            component = p.shallow_clone()
            node = self.Node(nid, component)

            self.nodes[nid] = node

            for estr in component.IN:
                actual_estr = component.get_actual_edge(estr)
                node.in_dict[estr] = actual_estr

                e = self.get_or_create_edge(actual_estr)
                e['dest'].append(nid)
                node.indegree += 1
                node.in_list.append(e)
                
            for estr in component.OUT:
                actual_estr = component.get_actual_edge(estr)
                node.out_dict[estr] = actual_estr
                
                e = self.get_or_create_edge(actual_estr)
                if e['src'] != None:
                    raise Exception('Too many sources for ' + actual_estr + ' as ' + estr)
                e['src'] = nid
                node.outdegree += 1
                node.out_list.append(e)
                
        self.top_sort()

        self.graph = {
            'nodes': self.nodes,
            'edges': self.edges,
        }

    def get_actual_edge(self, estr):
        return self.wire_assignments[estr]
        
    def validate_config(self):
        for estr in self.IN + self.OUT:
            if estr not in self.wire_assignments:
                raise Exception('Incomplete wire configuration: ' + estr)
        
    def process(self, **kwargs):
        if not self.graph:
            self.build_graph()
            
        for estr in self.IN:
            self.edges[estr]['value'] = kwargs[estr]

        input_kwargs = {}
        for u in self.topo_ordering:
            for k in u.in_dict:
                input_kwargs[k] = self.edges[u.in_dict[k]]['value']
            output = u.component.process(**input_kwargs)
            for k,v in zip(u.component.OUT, output):
                self.edges[u.out_dict[k]]['value'] = v

        return [self.edges[k]['value'] for k in self.OUT]

    def eval(self, **kwargs):
        return self.process(**kwargs)
    
    def eval_single(self, **kwargs):
        return self.process(**kwargs)[0]

class WireFactory:
    __instance = None
    
    @staticmethod
    def get_instance():
        if WireFactory.__instance == None:
            WireFactory()

        return WireFactory.__instance

    def __getattr__(self, name):
        return name
    
    def __init__(self):
        if WireFactory.__instance != None:
            raise Exception('You should not try to instatiate WireFactory directly')

        WireFactory.__instance = self
        self.wire_dict = {}
        
w = WireFactory.get_instance()


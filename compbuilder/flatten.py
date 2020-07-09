from collections import deque
from compbuilder import Component, Wire, w
from visual_gates import *

##############################################
class Net:
    class Connection:
        def __init__(self,net,component,wire,net_slice):
            self.component = component  # component attached to this net
            self.wire = wire            # component's port of attachment
            self.slice = net_slice      # part of the net attached to wire

        def __repr__(self):
            start,stop,_ = self.slice.indices(self.net.width)
            return '{}:{} -> {}[{}:{}]'.format(
                    self.component.name,
                    self.wire,
                    self.net.name,
                    start,
                    stop-1,
                    )

    def __init__(self,name,width,signal=None):
        self.name = name
        self.width = width
        self.signal = signal  # current signal value of the net
        self.sources = []     # connections to the signal sources of this net
        self.targets = []     # connections to all targets on this net
        self.prelist = set()  # set of prerequisites
        self.postlist = set() # set of nets affected by this one
        self.level = None     # level in the topological sorting order

    def add_connection(self,component,wire,dir,net_slice):
        if dir == 'in':
            conn = Net.Connection(self,component,wire,net_slice)
            #print('  TARGET:',conn)
            self.targets.append(conn)
        elif dir == 'out':
            conn = Net.Connection(self,component,wire,net_slice)
            #print('  SOURCE:',conn)
            self.sources.append(conn)
        else:
            raise Exception('Invalid wire direction')

    def print(self):
        print('{} -> {}'.format(
            self.source,
            self.targets,
            ))

    def __repr__(self):
        return f'{self.name}({self.width})'

    def __lt__(self,o):
        return self.level < o.level

##############################################
def _create_nets(self,outer,netlist,complist,path):
    self.initialize()
    self.wiring = {}   # map local pin to (net,slice)
    self.name = '{}{}'.format(self.get_gate_name(),path)

    # define default LATCH and TRIGGER for convenience
    if not hasattr(self,'LATCH'):
        self.LATCH = {}
    if not hasattr(self,'TRIGGER'):
        # for component without TRIGGER attribute defined, all inputs are
        # considered triggers
        self.TRIGGER = self.IN

    ports = [(w,'in') for w in self.IN]
    ports += [(w,'out') for w in self.OUT]
    for w,dir in ports:
        if outer is not None:
            # This is an internal component.  Assign the corresponding outer
            # net to each of the inputs and outputs, while maintaining matched
            # slicing between net and component's wire
            outer_wire = self.wire_assignments[w.name]
            #print(f'{dir} {outer}:{outer_wire} -> {self}:{w}')
            net,outer_slice = outer.wiring[outer_wire.get_key()]
            #print(outer_wire.slice,outer_slice)
            wire_slice = outer_wire.slice or slice(0,w.width)
            offset,_,_ = outer_slice.indices(net.width)
            wstart,wstop,_ = wire_slice.indices(net.width)
            net_slice = slice(wstart+offset, wstop+offset)
        else:
            # This is the outermost component.  Create a new net for each of
            # the inputs/outputs.
            net = Net(f'{self.name}:{w.name}',w.width)
            net_slice = w.slice or slice(0,w.width)
            netlist.append(net)
        self.wiring[w.get_key()] = (net,net_slice)

        # only keep track of connections for outermost and innermost
        # components, i.e., external inputs/outputs and primitive components
        if not self.PARTS:  # primitive component
            net.add_connection(self,w,dir,net_slice)
        if outer is None:   # whole component
            # swap in/out because external inputs serve as outputs for
            # internal components and vice versa
            dir_swap = 'in' if dir == 'out' else 'out'
            net.add_connection(self,w,dir_swap,net_slice)

    if self.PARTS:
        # create a net for each of the internal wires
        for key,edge in self.edges.items():
            if key not in self.wiring: # internal wires
                name,width = key
                net = Net(f'{self.name}:{name}',width)
                self.wiring[key] = (net,slice(0,width))
                netlist.append(net)
        # recusively assign nets for each of the internal components
        for inner in self.internal_components:
            inner_path = path+f'-{inner.node.id}'
            inner._create_nets(self,netlist,complist,inner_path)
    else:
        # primitive component; put it in the primitive component list
        complist.append(self)

        # create pre-/post-requisite net list via this primitive, skip all
        # non-trigger pins
        for wout in self.OUT:
            out_net,nslice = self.wiring[wout.get_key()]
            for win in self.IN:
                if win.get_key() not in [w.get_key() for w in self.TRIGGER]:
                    continue
                in_net,nslice = self.wiring[win.get_key()]
                out_net.prelist.add(in_net)
                in_net.postlist.add(out_net)

##############################################
def create_nets(self):
    netlist = []
    complist = []
    self._create_nets(None,netlist,complist,'')
    return netlist,complist

##############################################
def topsort_nets(self):
    resolved = set()
    # start with inputs and latches
    unexplored = deque(self.wiring[w.get_key()][0] for w in self.IN)
    for p in self.primitives:
        for latch in p.LATCH:
            unexplored.append(p.wiring[latch.get_key()][0])

    for u in unexplored:
        u.level = 0
    while unexplored:
        current = unexplored.popleft()
        #print('current',current)
        if current in resolved:
            continue
        pending = [p for p in current.prelist if p not in resolved]
        #print('pending',pending)
        if pending:
            unexplored.append(current)
        else:
            resolved.add(current)
            for net in current.postlist:
                net.level = current.level + 1
                unexplored.append(net)

##############################################
def trigger(self):
    '''
    Trigger this primitive part by processing values from input nets and
    store results in output nets.
    '''
    if self.PARTS:
        raise Exception('This must be called by a primitive component only')
    inputs = {}
    for w in self.IN:
        net,nslice = self.wiring[w.get_key()]
        inputs[w.name] = net.signal[nslice]
    outputs = self.process(**inputs)
    for k in self.OUT:
        signal = outputs[k.name]
        estr = k.get_key()
        net,nslice = self.wiring[estr]
        net.signal = net.signal or Signal(0,net.width)
        net.signal.set_slice(nslice,signal)

##############################################
def update(self,**inputs):
    '''
    Update net signals with the specified input changes.  Return output
    signals.
    '''
    # populate input nets
    for w in self.IN:
        if w.name in inputs:
            net,_ = self.wiring[w.get_key()]
            net.signal = inputs[w.name]

    # populate the remaining nets by their topological ordering
    # (netlist must have already been topologically sorted)
    for net in self.netlist:
        for component in [s.component for s in net.sources]:
            if component.PARTS: # only consider primitives
                continue
            component.trigger()

    # extract outputs
    outputs = {}
    for w in self.OUT:
        net,_ = self.wiring[w.get_key()]
        outputs[w.name] = net.signal

    return outputs

##############################################
def flatten(self):
    self.netlist, self.primitives = self.create_nets()
    self.topsort_nets()
    self.netlist.sort()

    # instantiate net signals to zero and run update once to make their logic
    # values consistent
    for net in self.netlist:
        net.signal = Signal(0,net.width)
    self.update()

##############################################
def component_repr(self):
    if hasattr(self,'name'):
        return self.name
    else:
        return '{}@{:x}'.format(self.get_gate_name(),id(self))

##############################################
def wire_repr(self):
    if self.width == 1:
        prefix = 'w'
    else:
        prefix = f'w({self.width})'
    if self.slice:
        start,stop,_ = self.slice.indices(self.width)
        suffix = f'[{start}:{stop-1}]'
    else:
        suffix = ''
    return f'{prefix}.{self.name}{suffix}'

##############################################
setattr(Component,'__repr__',component_repr)
setattr(Component,'flatten',flatten)
setattr(Component,'_create_nets',_create_nets)
setattr(Component,'create_nets',create_nets)
setattr(Component,'update',update)
setattr(Component,'topsort_nets',topsort_nets)
setattr(Component,'trigger',trigger)
setattr(Wire,'__repr__',wire_repr)

from collections import deque
from compbuilder import Component, Wire, w, Signal

def remap_slice(net_width,net_slice,pin_width,pin_slice):
    '''
    Remap slice relative to local pin wiring into slice relative to global net
    >>> remap_slice(1,None,1,None)  # single-bit, default net and pin slices
    slice(0, 1, None)

    >>> remap_slice(8,None,4,None) # 8-bit net, 4-bit pin, default slices
    slice(0, 4, None)

    >>> remap_slice(8,slice(0,4),2,slice(0,2))
    slice(0, 2, None)

    >>> remap_slice(8,slice(4,8),4,slice(0,4))
    slice(4, 8, None)

    >>> remap_slice(8,slice(4,8),2,slice(2,4))
    slice(6, 8, None)
    '''
    pin_slice = pin_slice or slice(0,pin_width)
    net_slice = net_slice or slice(0,net_width)
    offset,_,_ = net_slice.indices(net_width)
    wstart,wstop,_ = pin_slice.indices(net_width)
    return slice(wstart+offset, wstop+offset)

##############################################
class Net:
    class Connection:
        def __init__(self,net,component,wire,net_slice):
            self.component = component  # component attached to this net
            self.wire = wire            # component's port of attachment
            self.slice = net_slice      # part of the net attached to wire
            self.net = net
            
        def __repr__(self):
            start,stop,_ = self.slice.indices(self.net.width)
            return '{}:{} -> {}[{}..{}]'.format(
                    self.component.name,
                    self.wire,
                    self.net.name,
                    start,
                    stop-1,
                    )

    def __init__(self,name,width,signal=None):
        self.name = name
        self.width = width
        self.signal = signal # current signal value of the net
        self.transient_signal = Signal(0,width) # signal's transient state
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
            net_slice = remap_slice(net.width, outer_slice,
                                    outer_wire.width, outer_wire.slice)
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
        for node in self.nodes.values():
            for i,w in enumerate([*node.in_wires.values(),*node.out_wires.values()]):
                if w.get_key() not in self.wiring: # internal wires
                    net_name = f'{self.name}:{w.name}'
                    if w.is_constant:
                        net = Net(net_name,w.width,signal=w.get_constant_signal())
                    else:
                        net = Net(net_name,w.width)
                    self.wiring[w.get_key()] = (net,slice(0,w.width))
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
    unexplored = deque()

    # start with inputs, constant wires, and latches
    unexplored.extend(self.wiring[w.get_key()][0] for w in self.IN)
    #print('unexplored init1:',unexplored)
    unexplored.extend(net for net in self.netlist if net.signal is not None)
    #print('unexplored init2:',unexplored)
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
    store results in output nets.  To avoid race conditions, the trigger
    process stores results in transient net signals (which must have already
    been prepared).  The new signals must later on be copied over the current
    signals before triggering the components attached to the nets in the next
    topological level.  Return a set of affected nets.
    '''
    if self.PARTS:
        raise Exception('This must be called by a primitive component only')
    affected = set()
    inputs = {}
    for w in self.IN:
        net,nslice = self.wiring[w.get_key()]
        inputs[w.name] = net.signal[nslice]
    outputs = self.process(**inputs)
    for k in self.OUT:
        signal = outputs[k.name]
        estr = k.get_key()
        net,nslice = self.wiring[estr]
        net.transient_signal.set_slice(nslice,signal)
        affected.add(net)
    return affected

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
    current_level = 0
    transient_nets = set()
    for net in self.netlist:
        if net.level != current_level:
            # new level -- update previous-level nets with their transient
            # signals
            for tnet in transient_nets:
                tnet.signal.value = tnet.transient_signal.value
            transient_nets.clear()
            current_level = net.level
        for component in [s.component for s in net.sources]:
            if not component.PARTS: # trigger primitives only
                affected = component.trigger()
                transient_nets.update(affected)
    # update from the transient signals in the final level
    for tnet in transient_nets:
        tnet.signal.value = tnet.transient_signal.value

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

    # instantiate net signals to zero, except constant nets, and run update
    # once to make their logic values consistent
    for net in self.netlist:
        if net.signal is None:
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
    else:
        start,stop = 0,self.width
    if self.width == 1 and start == 0:
        suffix = ''
    elif stop == start+1:
        suffix = f'[{start}]'
    else:
        suffix = f'[{start}..{stop-1}]'
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

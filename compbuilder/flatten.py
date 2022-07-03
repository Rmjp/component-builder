from collections import deque
from compbuilder import Component, Wire, w, Signal
from compbuilder.tracing import trace

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
        if self.is_js_primitive():  # primitive component
            net.add_connection(self,w,dir,net_slice)
        if outer is None:   # whole component
            # swap in/out because external inputs serve as outputs for
            # internal components and vice versa
            dir_swap = 'in' if dir == 'out' else 'out'
            net.add_connection(self,w,dir_swap,net_slice)

    if not self.is_js_primitive():
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
    resolving_list = []
    resolving_set = set()

    # start with constant wires, inputs, and latches
    resolving_list.extend(net for net in self.netlist if net.signal is not None)
    resolving_list.extend(self.wiring[w.get_key()][0] for w in self.IN)
    for p in self.primitives:
        for latch in p.LATCH:
            resolving_list.append(p.wiring[latch.get_key()][0])

    resolving_set.update(resolving_list)
    # we have to use dict to preserve insertion order (python >= 3.6)
    resolving = deque(dict.fromkeys(resolving_list))

    total_edges = sum(len(n.postlist) for n in self.netlist)

    for u in resolving:
        u.level = 0
    while resolving:
        #print('RESOLVING:', resolving)
        #print('RESOLVED:', resolved)
        current = resolving.popleft()
        resolving_set.remove(current)
        resolved.add(current)
        #print(f'{len(resolved)}/{len(self.netlist)} nets resolved')
        for net in current.postlist:
            net.level = current.level + 1
            pre = [p for p in net.prelist if p not in resolved]
            if not pre and net not in resolving_set:
                resolving.append(net)
                resolving_set.add(net)
            #    print(net,'resolved')
            #    if net in resolved:
            #        raise Exception(f'Loop detected at net {net} pre={net.prelist}')
            #else:
            #    print(net,'<-',pre)

    # XXX do loop check here (or should loop have already been detected by the
    # generic component class?)

    # XXX loop checking may be difficult to do in this function, especially
    # with primitive clocked components that also immediately react to input
    # such as fast RAM.  The reason is this function assumes that output of
    # clocked components have no dependency.

    # check for unreachability
    for net in self.netlist:
        if net.level is None:
            raise Exception(f'Net {net} is unreachable')


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
    if not self.is_js_primitive():
        raise Exception('This must be called by a primitive component only')
    affected = set()
    inputs = {}
    for w in self.IN:
        net,nslice = self.wiring[w.get_key()]
        inputs[w.name] = net.signal[nslice]
    outputs = self.process_interact(**inputs)
    for k in self.OUT:
        signal = outputs[k.name]
        estr = k.get_key()
        net,nslice = self.wiring[estr]
        net.transient_signal.set_slice(nslice,signal)
        if net.transient_signal.value != net.signal.value:
            affected.add(net)
    return affected

##############################################
def update_full(self,**inputs):
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
            if component.is_js_primitive(): # trigger primitives only
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
def update(self,**inputs):
    '''
    Optimally update net signals with the specified input changes.  Return output
    signals.
    '''
    import heapq
    dirty = []
    transient_nets = set()
    # populate input nets
    for w in self.IN:
        if w.name in inputs:
            net,_ = self.wiring[w.get_key()]
            net.transient_signal = inputs[w.name]
            transient_nets.add(net)
            for affected_net in net.postlist:
                heapq.heappush(dirty, affected_net)

    # populate the remaining nets by their topological ordering
    # (netlist must have already been topologically sorted)
    current_level = 0
    seen = set()
    while dirty:
        net = heapq.heappop(dirty)
        if net in seen:
            continue
        else:
            seen.add(net)
        if net.level != current_level:
            # new level -- update previous-level nets with their transient
            # signals
            for tnet in transient_nets:
                tnet.signal.value = tnet.transient_signal.value
            transient_nets.clear()
            current_level = net.level
        for component in [s.component for s in net.sources]:
            if component.is_js_primitive(): # trigger primitives only
                changes = component.trigger()
                transient_nets.update(changes)
                for change in changes:
                    for affected_net in change.postlist:
                        heapq.heappush(dirty,affected_net)
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
    # run trace with dummy inputs as an attempt to detect loops
    #tmpcomp = self.__class__()
    #inputs = {}
    #for inwire in tmpcomp.IN:
    #    if inwire.name != 'clk':
    #        inputs[inwire.name] = [0]
    #trace(tmpcomp, inputs, [])

    if hasattr(self,'netlist'):
        return
    self.netlist, self.primitives = self.create_nets()
    self.topsort_nets()
    self.netlist.sort()

    # instantiate net signals to zero, except constant nets, and run update
    # once to make their logic values consistent
    for net in self.netlist:
        if net.signal is None:
            net.signal = Signal(0,net.width)
    self.update_full()

##############################################
def component_repr(self):
    if hasattr(self,'name'):
        return self.name
    else:
        return '{}@{:x}'.format(self.get_gate_name(),id(self))

##############################################
def wire_repr(self):
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
    return f'{self.name}{suffix}'

##############################################
def report(cls_or_instance):
    from collections import Counter
    if isinstance(cls_or_instance,type):
        comp = cls_or_instance()
    else:
        comp = cls_or_instance
    comp.init_interact()
    comp.flatten()
    counter = Counter([p.get_gate_name() for p in comp.primitives])
    print(f'Total primitives: {len(comp.primitives)}')
    for gate,count in counter.items():
        print(f'  - {count} {gate}(s)')
    print(f'Total nets: {len(comp.netlist)}')
    print(f'Longest path length: {comp.netlist[-1].level}')

##############################################
setattr(Component,'__repr__',component_repr)
setattr(Component,'flatten',flatten)
setattr(Component,'_create_nets',_create_nets)
setattr(Component,'create_nets',create_nets)
setattr(Component,'update',update)
setattr(Component,'update_full',update_full)
setattr(Component,'topsort_nets',topsort_nets)
setattr(Component,'trigger',trigger)
setattr(Wire,'__repr__',wire_repr)

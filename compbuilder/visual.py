import re
import math
from copy import deepcopy
from textwrap import indent,dedent
import json
from . import flatten
from . import Component,Signal,w

ASSETS_ROOT = "https://ecourse.cpe.ku.ac.th/component-builder/compbuilder"
ASSETS_TS = "20230728-1"
ELKJS_URL = "https://cdn.jsdelivr.net/npm/elkjs@0.8.2/lib/elk.bundled.js"

DEFAULT_LAYOUT_CONFIG = {
    'width' : 60,
    'port_spacing' : 20,
    'label_width' : 50,
    'label_height' : 10,
    'port_width' : 8,
    'port_height' : 8,
    'connector_width' : 20,
    'connector_height' : 16,
}

COMPOUND_GATE_JS_TEMPLATE = indent(dedent('''
  "{name}" : {{
    IN: [{inputs}],
    OUT: [{outputs}],
  }}'''),'  ')

PRIMITIVE_GATE_JS_TEMPLATE = indent(dedent('''
  "{name}" : {{
    IN: [{inputs}],
    OUT: [{outputs}],
    init: {init},
    process: {{
  {process}
    }}
  }}'''),'  ')

PROCESS_JS_TEMPLATE = ' '*4 + '"{pin}" : {function},'

_diagram_id = 1

################################
def _generate_net_wiring(net_wiring,netmap):
    net,nslice = net_wiring
    start,stop,_ = nslice.indices(net.width)
    return {
        'net' : netmap[net],
        'slice' : [start,stop-1],
    }

################################
def _generate_wiring(comp,netmap):
    wiring = {}
    for w in comp.IN + comp.OUT:
        wiring[w.name] = _generate_net_wiring(
                comp.wiring[w.get_key()],netmap)
    return wiring

################################
def get_wire_name(wire):
    '''
    Generate a string representing a signal from the specified wire with
    proper slicing notation.  Note that the notation is different from the
    notation used in Python.
    >>> get_wire_name(w.a)
    'a'
    >>> get_wire_name(w(8).a)
    'a[7..0]'
    >>> get_wire_name(w(8).a[2])
    'a[2]'
    >>> get_wire_name(w(8).a[2:3])
    'a[2]'
    >>> get_wire_name(w(8).a[1:5])
    'a[4..1]'
    '''
    if wire.slice:
        start,stop,_ = wire.slice.indices(wire.width)
    else:
        start = 0
        stop = wire.width
    if wire.width == 1:
        return wire.name
    elif start+1 == stop:
        return f'{wire.name}[{start}]'
    else:
        return f'{wire.name}[{stop-1}..{start}]'

################################
def get_wire_slice(wire):
    '''
    Generate a tuple containing the specified wire's name and its slice
    information
    >>> get_wire_slice(w.a)
    (0, 1)
    >>> get_wire_slice(w(8).a)
    (0, 8)
    >>> get_wire_slice(w(8).a[2])
    (2, 3)
    >>> get_wire_slice(w(8).a[2:3])
    (2, 3)
    >>> get_wire_slice(w(8).a[1:5])
    (1, 5)
    '''
    if wire.slice is None:
        start,stop = 0,wire.width
    else:
        start,stop,_ = wire.slice.indices(wire.width)
    return (start,stop)

################################
class VisualMixin:

    ################
    def _create_body(self,comp_id):
        body = {
            'id' : f'{comp_id}',
            'width' : self.config['width'],
            'height' : self.config['height'],
        }

        # add component label only when not empty
        if 'label' in self.config:
            body['labels'] = [{
                'text' : self.config['label'],
                'id' : f'L{comp_id}',
                'width' : self.config['label_width'],
                'height' : self.config['label_height'],
            }]

        # attach custom svg elements, if available
        if 'svg' in self.config:
            body['svg'] = self.config['svg']
        return body

    ################
    def _create_label(self,comp_id):
        label = self.config['label']
        return [{
            'text': label,
            'id': f'L{comp_id}',
            'width': 6*len(label),
            'height': self.config['label_height']
        }]

    ################
    def _create_port(self,wire,port_id,index,dir):
        side = {'in': 'WEST','out':'EAST'}[dir]
        port = {
            'id': f'P_{port_id}',
            'properties': {
              'port.side': side,
              'port.index': index,
            },
            'width': self.config['port_width'],
            'height': self.config['port_height'],
        }
        try:  # use configured port label if available
            label = self.config['ports'][wire.name]['label']
        except KeyError:
            label = wire.name

        if wire.width > 1:
            label += f'[{wire.width-1}..0]'

        if label:
            port['labels'] = [{
                'id' : f'LP{port_id}',
                'text' : label,
                'width' : 6*len(label),
                'height' : self.config['label_height'],
            }]

        return port

    ################
    def _create_connector(self,dir,port_id,text='',type='connector'):
        port_side = {'in':'EAST','out':'WEST'}[dir]
        if text:
            width = int(6*len(text)) + 16  # XXX magic
        else:
            width = self.config['connector_width']
        height = self.config['connector_height']
        obj = {
            'id' : f'C_{port_id}',
            'type' : type,
            'direction' : dir,
            'width' : width,
            'height' : height,
            'ports' : [{
                'id': f'CP_{port_id}',
                'properties': {
                  'port.side': port_side,
                },
                'width': 0,
                'height': 0,
                'type': 'connector',
            }],
            'properties': {
                'portConstraints': 'FIXED_ORDER',
                'nodeLabels.placement': '[H_CENTER, V_CENTER, INSIDE]'
            },
        }
        if text:
            obj['labels'] = [{
                'text': text,
                'id': f'CL_{port_id}',
                'width': width,
                'height': height,
            }]
        return obj

    ################
    def _create_edge(self,src,dst):
        return { 'sources' : [src], 'targets' : [dst] }

    ################
    def _generate_elk(self,depth,netmap,base_id=''):
        expanded = hasattr(self,'_expanded') and self._expanded
        self.config = deepcopy(DEFAULT_LAYOUT_CONFIG)
        # override with component's layout configuration (if exists) when it
        # is a primitive component or it is shown without internal components
        if (self.is_js_primitive() or (depth == 0 and not expanded)) \
                and hasattr(self,"LAYOUT_CONFIG"):
            self.config.update(self.LAYOUT_CONFIG)

        # port_map maintain mapping of (node-id,wire,slice) -> (ELK port-id)
        inner_port_map = {}
        if (depth == 0 and not expanded) or self.is_js_primitive(): # just create an IC box
            if 'height' not in self.config:
                # determine component's height from the maximum number of
                # ports on each side
                port_max = max(len(self.IN),len(self.OUT))
                self.config['height'] = port_max * self.config['port_spacing']
            if 'label' not in self.config:
                self.config['label'] = self.name
            box = self._create_body(self.name)
            if 'widget' in self.config:
                box['widget'] = self.config['widget']
        else:
            children = []
            for i,node in self.nodes.items():
                subcomp_id = f'{base_id}_{i}'
                subcomp,inner_port_map[i] = node.component._generate_elk(max(depth-1,0),netmap,subcomp_id)
                subcomp['node_id'] = node.id
                children.append(subcomp)
            # use original label when internal components are shown
            self.config['label'] = self.name
            box = {
                'id' : self.name,
                'children' : children,
                }

        # add input and output ports to the left and right sides of the
        # component box, respectively;
        # also maintain port_map to be exposed to the outer component
        port_map = {}  # map (component's pin) -> (ELK port-id)
        elk_ports = []
        ports = [(w,'in') for w in self.IN[::-1]]
        ports += [(w,'out') for w in self.OUT]
        for i,(pin,dir) in enumerate(ports):
            port_id = f'{self.name}:{pin.name}'
            elk_port = self._create_port(pin,port_id,i,dir)
            # attach wire's metadata to help styling
            netwire = _generate_net_wiring(self.wiring[pin.get_key()],netmap)
            netwire['name'] = pin.name
            elk_port['wire'] = netwire
            elk_port['name'] = pin.name
            elk_ports.append(elk_port)
            port_map[pin.get_key()] = elk_port['id']
        box['ports'] = elk_ports

        # when internal components are shown, also add edges to represent
        # internal wiring
        if (depth > 0 or expanded) and not self.is_js_primitive():
            # maintain a data structure that allows inquiries of an internal
            # wire's source and destination ELK ports by its name and slicing
            # wires: wire-key -> (net,dir,[source...],[dest...])
            # where each source and dest is of the form (wire,ELK-port-id,net-slice)
            wires = {}
            for pin in self.IN:
                net,nslice = self.wiring[pin.get_key()]
                _,_,sources,_ = wires.setdefault(pin.get_key(), (net,'in',[],[]))
                entry = (pin, port_map[pin.get_key()], nslice)
                sources.append(entry)
            for pin in self.OUT:
                net,nslice = self.wiring[pin.get_key()]
                _,_,_,dests = wires.setdefault(pin.get_key(), (net,'out',[],[]))
                entry = (pin, port_map[pin.get_key()], nslice)
                dests.append(entry)
            constants = set()
            for nid,node in self.nodes.items():
                comp = node.component
                for pin in comp.IN:
                    wire = comp.get_actual_wire(pin.name)
                    net,nslice = comp.wiring[pin.get_key()]
                    _,_,sources,dests = wires.setdefault(wire.get_key(), (net,'in',[],[]))
                    entry = (comp.get_actual_wire(pin.name),
                             inner_port_map[nid][pin.get_key()],
                             nslice)
                    dests.append(entry)
                    if wire.is_constant and wire.name not in constants:
                        # constant wire; create a source connector for it
                        # also make sure we have only one constant pad for
                        # identical constant values
                        constants.add(wire.name)
                        netwire = _generate_net_wiring( (net,nslice), netmap)
                        digits = math.ceil(wire.width/4)
                        connector = self._create_connector(
                                'in',
                                f'{node.component.name}:{pin.name}',
                                f'{wire.get_constant_signal().get():0{digits}X}',
                                type='constant')
                        connector['wire'] = netwire
                        entry = (wire, connector['ports'][0]['id'], nslice)
                        sources.append(entry)
                        box['children'].append(connector)
                for pin in comp.OUT:
                    wire = comp.get_actual_wire(pin.name)
                    net,nslice = comp.wiring[pin.get_key()]
                    _,_,sources,_ = wires.setdefault(wire.get_key(), (net,'out',[],[]))
                    entry = (comp.get_actual_wire(pin.name),
                             inner_port_map[nid][pin.get_key()],
                             nslice)
                    sources.append(entry)
            #for w in wires:
            #    net,dir,sources,dests = wires[w]
            #    print(w)
            #    print(' net:', net)
            #    print(' dir:', dir)
            #    print(' src:', sources)
            #    print(' dst:', dests)

            # define edges from all the wire connections generated above
            edges = []
            for net,dir,sources,dests in wires.values():
                # create an edge between source/dest with overlapping slices
                for swire,sport,sslice in sources:
                    sstart,sstop,_ = sslice.indices(net.width)
                    for dwire,dport,dslice in dests:
                        dstart,dstop,_ = dslice.indices(net.width)
                        if not(sstart < dstop and dstart < sstop):
                            continue # not overlapping
                        edge = self._create_edge(sport,dport)
                        # attach wire's metadata to help styling
                        if sslice.stop - sslice.start < dslice.stop - dslice.start:
                            # source's slice is a subset of destination's
                            wslice = sslice
                            wire = swire
                        else:
                            # destination's slice is a subset of source's
                            wslice = dslice
                            wire = dwire
                        netwire = _generate_net_wiring((net,wslice),netmap)
                        edge['wire'] = netwire
                        if wire.is_constant:
                            edge['name'] = f'const({wire.width})'
                        else:
                            edge['dir'] = dir
                            edge['name'] = repr(wire)
                        edges.append(edge)

            # enumerate all edges and give them proper IDs
            for i,edge in enumerate(edges):
                edge['id'] = f'E{base_id}_{i}'

            # attach edges to the box
            box['edges'] = edges

        # give the box a final touch
        box['gate'] = self.get_gate_name()
        box['labels'] = self._create_label(base_id)
        box['properties'] = {
            'portConstraints': 'FIXED_ORDER',
            'nodeLabels.placement': '[H_LEFT, V_TOP, OUTSIDE]',
            'portLabels.placement': 'OUTSIDE',
        }
        return box, port_map

    ################
    def _generate_part_config(self):
        name = self.get_gate_name()
        inputs = ','.join(f'"{w.name}"' for w in self.IN)
        outputs = ','.join(f'"{w.name}"' for w in self.OUT)
        if not self.is_js_primitive():
            return COMPOUND_GATE_JS_TEMPLATE.format(
                name=name,
                inputs=inputs,
                outputs=outputs,
            )
        else:
            process = [PROCESS_JS_TEMPLATE.format(pin=k,function=v or 'null')
                        for k,v in self.process_interact.js.items()]
            if hasattr(self.__init__,'js'):
                init = self.__init__.js
            else:
                init = 'null'
            return PRIMITIVE_GATE_JS_TEMPLATE.format(
                name=name,
                inputs=inputs,
                outputs=outputs,
                init=init,
                process='\n'.join(process),
            )

    ################
    def generate_elk(self,depth=0,clockgen=None,expand=None,**kwargs):
        # mark all subcomponents that need to be expanded
        expand = expand or []
        for e in expand:
            seq = []
            current = self
            current._expanded = True
            for id in e.split('-')[1:]: # traverse inside the expanded part
                id = int(id)
                seq.append(id)
                try:
                    current = current.nodes[id].component
                    current._expanded = True
                except KeyError:
                    break
            if current.name != e:
                raise Exception(f'Part {e} not found')

        # generate main component box
        layout,port_map = self._generate_elk(depth,self.netmap,**kwargs)

        # add I/O connectors, and optional clock generator, around the main
        # component
        widgets = []
        conlinks = []
        ports = [(p,'in') for p in self.IN[::-1]]
        ports += [(p,'out') for p in self.OUT]
        for i,(port,dir) in enumerate(ports):
            netwire = _generate_net_wiring(
                    self.wiring[port.get_key()],self.netmap)
            netwire['name'] = port.name
            if port.name == clockgen:
                # generate a clock generator widget
                clk = ClockGenerator(clk=w.clk)
                clk.flatten()
                clknet = clk.netlist[0]
                self.netmap[clknet] = netwire['net']
                clk_layout,clk_portmap = clk._generate_elk(depth,self.netmap)
                widget = clk_layout
            else:
                # generate a generic I/O connector
                if port.width > 1:  # generate placeholder for signal's value
                    value = '0'*math.ceil(port.width/4)
                else:
                    value = ''
                connector = self._create_connector(dir,f'{self.name}:{port.name}',value)
                connector['wire'] = netwire
                widget = connector
            port_id = port_map[port.get_key()]
            widgets.append(widget)
            connector_id = widget['ports'][0]['id']
            conlink = self._create_edge(connector_id,port_id)
            conlink['id'] = f'CE_{i}'
            conlink['wire'] = netwire
            conlink['name'] = repr(port)
            conlinks.append(conlink)

        return {
            'id' : '$root',
            'children' : [layout] + widgets,
            'edges' : conlinks,
        }

    ################
    def _generate_node_map(self,elk,node_map,prefix):
        if 'children' not in elk:
            return
        for c in elk['children']:
            part_expr = f'{prefix}.parts[{c["node_id"]}]'
            node_map[c['id']] = part_expr
            self._generate_node_map(c,node_map,part_expr)

    ################
    def _generate_component_config(self):
        # create component->index mappings
        # component list consists of the main component itself, and all its
        # primitives and wirings
        partmap = {}
        for i,part in enumerate([self] + self.primitives):
            partmap[part] = i

        # create net->index mappings
        self.netmap = {}
        for i,net in enumerate(self.netlist):
            self.netmap[net] = i

        # generate primitive component wiring 
        parts = []
        for comp in [self] + self.primitives:
            wiring = _generate_wiring(comp,self.netmap)
            parts.append({
                'name': comp.name,
                'config': comp.get_gate_name(),
                'wiring': wiring,
            })

        # generate netlist config
        nets = []
        for net in self.netlist:
            sources = []
            for source in net.sources:
                start,stop,_ = source.slice.indices(net.width)
                if (start,stop) == (0,1): # single wire; omit slicing
                    sources.append({
                        'part' : partmap[source.component],
                        'wire' : source.wire.name,
                    })
                else:
                    sources.append({
                        'part' : partmap[source.component],
                        'wire' : source.wire.name,
                        'slice' : [start,stop-1],
                    })
            net_data = {
                'name' : net.name,
                'level' : net.level,
                'width' : net.width,
                'signal' : net.signal.get(),
                'sources' : sources,
                'wiring' : _generate_wiring(comp,self.netmap),
            }
            triggered = []
            for part, wname in net.triggered:
                triggered.append({
                    'part': partmap[part],
                    'process': wname,
                })

            if net.triggered:
                net_data['triggered'] = triggered
            nets.append(net_data)

        # combine all configs
        config = {
            'parts': parts,
            'nets': nets,
        }
        return config

    ##############################################
    def is_js_primitive(self):
        return hasattr(self,'process_interact')

    ##############################################
    def generate_js(self,
                    indent=None,
                    depth=0,
                    clockgen=None,
                    expand=None,
                    probe=None,
                    input_script=None,
                    **kwargs):
        self.flatten()
        lines = []

        # main component configuration
        comp_js = json.dumps(self._generate_component_config(),indent=indent)
        lines.append('var compConfig = ' + comp_js + ';')

        # main component's wiring and all used primitives
        used_primitives = {p.__class__:p for p in self.primitives}
        part_configs_js = ','.join(p._generate_part_config()
                for p in [self]+list(used_primitives.values()))
        lines.append('')
        lines.append('compConfig.partConfigs = {' + part_configs_js + '\n};')

        # instantiate the main component
        lines.append('')
        lines.append('var component = new Component(compConfig);')

        # ELK graph
        lines.append('')
        elk = self.generate_elk(depth=depth,clockgen=clockgen,expand=expand,**kwargs)
        lines.append('var graph = '
                + json.dumps(elk,indent=indent)
                + ';')

        # Signal probe list
        if probe is not None:
            probe_list = []
            px, py = 10, 10  # default start position
            for pstr in probe:
                comp, wire, wslice, net, nslice, pos = self.resolve_probe(pstr)
                disp_name = f'{comp.name}:{wire}'
                if wslice.start == wslice.stop-1:
                    if wslice.start != 0: # single-bit indexing
                        disp_name += f'[{wslice.start}]'
                else: # multi-bit slicing
                    disp_name += f'[{wslice.stop-1}..{wslice.start}]'

                if pos:
                    px, py = pos
                else:
                    py += 30

                probe_list.append({
                    'name': disp_name,
                    'netId': self.netmap[net],
                    'slice': [nslice.start, nslice.stop-1],
                    'x': px,
                    'y': py,
                })
        else:
            probe_list = []
        lines.append('')
        lines.append('var probe = '
                + json.dumps(probe_list)
                + ';')

        lines.append('')
        input_script = input_script or None
        lines.append('var config = {')
        lines.append('  component: component,')
        lines.append('  graph: graph,')
        lines.append('  probe: probe,')
        lines.append('  inputScript: {}'.format(json.dumps(input_script)))
        lines.append('};')


        return '\n'.join(lines)

    ##############################################
    PROBE_EXPR_RE = re.compile(
        r'^([A-Za-z][A-Za-z0-9]*(-\d+)*):(\w+)(\[(\d+)((:|\.\.)(\d+))?\])?(:\d+:\d+)?$')
    def resolve_probe(self, pstr):
        """
        Parse and resolve a probe expression.  This component must have been
        flattened before invoking this method.  If successful, this method
        then returns a tuple (component, wirename, wire_slice, net, net_slice, pos).
        """
        m = self.PROBE_EXPR_RE.match(pstr)
        if m is None:
            raise ValueError(f'Invalid probe expression: {pstr}')
        comp_id = m.group(1)
        if '-' in comp_id:
            path = [int(x) for x in comp_id.split('-')[1:]]
            comp_type = comp_id.split('-', 1)[0]
        else:
            path = []
            comp_type = comp_id

        # traverse the path to find the specified component
        comp = self
        for idx in path:
            comp = comp.internal_components[idx-1]

        # check if the actual component type is the same as the expression
        if comp.get_gate_name() != comp_type:
            raise ValueError(
                'Component type mismatched: '
                f'{comp.get_gate_name()} vs. {comp_type}')

        wire_name = m.group(3)
        for wire_key in comp.wiring:
            if wire_name == wire_key[0]:
                break
        else:
            raise ValueError(f"'{comp_type}' component has no pin or wire '{wire_name}'")

        _, wire_width = wire_key
        net, wire_slice = comp.wiring[wire_key]
        stop = m.group(5)
        mode = m.group(7)
        start = m.group(8)
        if start is None and stop is None:  # no slicing; take full width
            start = 0
            stop = wire_width
        else:
            start = int(start)
            if stop is not None:
                stop = int(stop)
            else:
                stop = start + 1  # no stop; treat as a single bit
        if mode == '..':
            stop += 1  # inclusive mode; include stop itself
        probe_slice = slice(start, stop)
        probe_width = stop - start

        if probe_width < 1:
            raise ValueError(f'Invalid wire slicing: {pstr}')
        if start >= wire_width or stop > wire_width:
            raise ValueError(
                f'Out-of-bound slicing: {pstr}; '
                f'allowed range is {wire_width-1}..0')

        pos = m.group(9)
        if pos is not None:
            pos = [int(c) for c in pos[1:].split(':')]

        net_slice = flatten.remap_slice(net.width, wire_slice, probe_width, probe_slice)
        return comp, wire_name, probe_slice, net, net_slice, pos


################################
class ClockGenerator(VisualMixin,Component):
    IN = []
    OUT = [w.clk]

    PARTS = []
    LATCH = [(w.clk, None)]

    LAYOUT_CONFIG = {
        'label' : '',
        'ports' : {  # hide all port labels
            'clk' : {'label' : ''},
        },
        'widget': 'clock',
    }

    def process(self,**inputs):
        pass
    def process_interact(self,**inputs):
        # always generate logic 0 in Python
        return {'clk': Signal(0)}
    # will be replaced by clock widget in JavaScript
    process_interact.js = None

################################
def interact_vs():
    import IPython.display as DISP
    DISP.display_javascript(DISP.Javascript(data="""   
        define = undefined;                                                                     
    """))
    assets_root = ASSETS_ROOT
    assets_ts = ASSETS_TS
    libs = ["https://d3js.org/d3.v5.js", f"{ELKJS_URL}", f"{assets_root}/js/component.js?v={assets_ts}", f"{assets_root}/js/visual.js?v={assets_ts}", f"{assets_root}/js/widgets.js?v={assets_ts}"]
    DISP.display_javascript(DISP.Javascript(lib=libs, data="""                                      
"""))

def interact(component_class,
             depth=0,
             probe=None,
             expand=None,
             clockgen=False,
             input_script=None,
             **kwargs):
    """
    Visualizes a component interactively.  At the moment it only works in
    Google Colab, not in Jupyter Notebook or Jupyter Lab.  The visualization
    supports the following interactions:

    * A single-bit input can be toggled by clicking on the input pin.
    * A multi-bit input can be changed by entering a hexadecimal number in the
      box attached to the input pin.
    * Single-bit wires and output pins are highlighted in green when they have
      logic value of T.
    * Hovering a mouse pointer over a wire pops up a probe box displaying the
      wire's name and its current value.
    * Clicking on a wire makes its probe box permanent, which can be dragged
      and dropped anywhere in the visualization area.  Clicking on a probe box
      makes it disappear.

    Note that multi-bit wires are displayed with an inclusive notation as used
    by various computer archtecture textbooks.  That is, s[i..j] covers from
    ith bit to jth bit of s, as opposed to Python's notation, s[x:y], which
    covers from ith bit to (j-1)st bit, excluding jth bit.

    Parameters
    ----------
    component_class : Component
        A component type to be visualized interactively.

    depth : int, default 0
        How many levels inner components will be shown.

    probe : list of str, default None
        A list of probe-expressions whose current names and values will be
        constantly shown in the interactive component widget.  A probe
        expression can be of the following forms:

        - <component>:<wire>
        - <component>:<wire>[index]
        - <component>:<wire>[start:stop] (excluding stop)
        - <component>:<wire>[start..stop] (including stop)

        For examples:
        - HalfAdder-1:c
        - Mux16:x[4]
        - Mux16:x[4:8]
        - Mux16:x[7..4]

        In addition, a probe expression can be followed by a pair of integers
        to specify the display position relative to the interactive widget.
        For example, the expression 'HalfAdder-1:c:10:50' will show a probe
        box positioned at (10,50).

    expand : list of str, default None
        A list of names of the inner components whose internal structures will
        be shown at the depth of 1, regardless of the depth parameter's value.

    clockgen : True or False, default False
        When True, the clock input of the component will be attached to a
        clock generator widget which is more convenient to simulate a clock to
        all clocked components.  Without the clockgen, the clock pin must be
        transitioned from F to T manually to generate a cycle.  The clockgen
        provides the |> (play) button to generate clock cycles at the rate of
        1 Hz, and the |>|> (fast-forward) button at the rate of 20 Hz.  A
        one-shot cycle can be produced with the |>| button.

    input_script : a list of input signal triggers
        If available, each member specifies an input pin and its value as a
        dict. For examples:
        - [{'In':1}, {'addr':0x1234}, {'clk':1}, {'clk':0}]
    """
    import os
    if any('vscode' in key.lower() for key in os.environ):
        interact_vs()
    import IPython.display as DISP
    global _diagram_id

    # XXX specifying js and css file locations here is very hacky;
    # please find a better way
    DISP.display_html(DISP.HTML("""
        <script src="https://d3js.org/d3.v5.js"></script>
        <script src="{ELKJS_URL}"></script>
        <script src="{assets_root}/js/component.js?v={assets_ts}"></script>
        <script src="{assets_root}/js/visual.js?v={assets_ts}"></script>
        <script src="{assets_root}/js/widgets.js?v={assets_ts}"></script>
    """.format(assets_root=ASSETS_ROOT,assets_ts=ASSETS_TS,ELKJS_URL=ELKJS_URL)))

    component = component_class()
    component.init_interact()

    if clockgen:
        clockgen = 'clk'
    else:
        clockgen = None

    DISP.display_html(
        DISP.HTML('<script>' +
                  component.generate_js(depth=depth,
                                        probe=probe,
                                        expand=expand,
                                        clockgen=clockgen,
                                        input_script=input_script,
                                        **kwargs) +
                  '</script>'))
    DISP.display_html(DISP.HTML("""
        <link rel="stylesheet" type="text/css" href="{assets_root}/css/styles.css?v={assets_ts}" />
        <div id="interact-diagram-{diagram_id}"></div>
        <script>
          compbuilder.create("#interact-diagram-{diagram_id}",config);
        </script>
    """.format(assets_root=ASSETS_ROOT, assets_ts=ASSETS_TS, diagram_id=_diagram_id)))

    _diagram_id += 1

################################
def generate_html(html_file,component_class,clockgen=False,**kwargs):
    TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{component_name}</title>
<script src="https://d3js.org/d3.v5.js"></script>
<script src="{ELKJS_URL}"></script>
<script src="{assets_root}/js/component.js?v={assets_ts}"></script>
<script src="{assets_root}/js/visual.js?v={assets_ts}"></script>
<script src="{assets_root}/js/widgets.js?v={assets_ts}"></script>
<script>
{js}
</script>
<link rel="stylesheet" type="text/css" href="{assets_root}/css/styles.css?v={assets_ts}" />
</head>

<body>
  <h2>Component: <i>{component_name}</i></h2>
  <div id="diagram"></div>
  <div id="status"></div>

  <script>
    compbuilder.create("#diagram",config,"#status");
  </script>
</body>
</html>
'''

    component = component_class()
    component.init_interact()

    if clockgen:
        clockgen = 'clk'
    else:
        clockgen = None

    with open(html_file,'w') as f:
        f.write(TEMPLATE.format(
            assets_root=ASSETS_ROOT,
            assets_ts=ASSETS_TS,
            ELKJS_URL=ELKJS_URL,
            component_name=component.get_gate_name(),
            js=component.generate_js(clockgen=clockgen,**kwargs),
        ))


interact_vs()
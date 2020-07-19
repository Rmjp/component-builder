import re
import math
from copy import deepcopy
from textwrap import indent,dedent
import json
import compbuilder.flatten

DEFAULT_LAYOUT_CONFIG = {
    'width' : 60,
    'port_spacing' : 20,
    'label_width' : 50,
    'label_height' : 10,
    'const_height' : 8,
    'port_width' : 8,
    'port_height' : 8,
    'connector_width' : 20,
    'connector_height' : 12,
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
    process: {{
  {process}
    }}
  }}'''),'  ')

PROCESS_JS_TEMPLATE = ' '*4 + '"{pin}" : {function},'

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
            'id': f'P:{port_id}',
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
            label += f'[{0}..{wire.width-1}]'

        if label:
            port['labels'] = [{
                'id' : f'LP{port_id}',
                'text' : label,
                'width' : 6*len(label),
                'height' : self.config['label_height'],
            }]

        return port

    ################
    def _create_connector(self,port_id,dir,bits):
        port_side = {'in':'EAST','out':'WEST'}[dir]
        if bits == 1:
            conn_width = self.config['connector_width']
        else: # bus wire
            # guestimate text width from bus width
            conn_width = int(6*bits/4) + 16
        return {
            'id' : f'C:{port_id}',
            'type' : 'connector',
            'direction' : dir,
            'bits' : bits,
            'width' : conn_width,
            'height' : self.config['connector_height'],
            'ports' : [{
                'id': f'C{dir[0].upper()}:{port_id}',
                'properties': {
                  'port.side': port_side,
                },
                'width': 0,
                'height': 0,
                'type': 'connector',
            }],
            'properties': {
                'portConstraints': 'FIXED_ORDER',
                'nodeLabels.placement': '[H_CENTER, V_TOP, OUTSIDE]'
            },
        }

    ################
    def _create_constant(self,value,bits,port_id):
        hex_digits = math.ceil(bits/4)
        label = f'{value:0{hex_digits}X}'
        width = 6*len(label)
        height = self.config['const_height']

        return {
            'id' : f'CNST_N:{port_id}',
            'width' : width + 10,
            'height' : height + 4,
            'type' : 'constant',
            'labels' : [{
                'text': str(label),
                'id': f'CNST_L:{port_id}',
                'width': width,
                'height': height,
            }],
            'ports' : [{
                'id': f'CNST_P:{port_id}',
                'properties': {
                  'port.side': 'EAST',
                },
                'width': 0,
                'height': 0,
            }],
            'properties': {
                'portConstraints': 'FIXED_ORDER',
                'nodeLabels.placement': '[H_CENTER, V_CENTER, INSIDE]'
            },
        }
    ################
    def _create_edge(self,src,dst):
        return { 'sources' : [src], "targets" : [dst] }

    ################
    def _generate_elk(self,depth,netmap,base_id=''):
        self.config = deepcopy(DEFAULT_LAYOUT_CONFIG)
        # override with component's layout configuration (if exists) when it
        # is a primitive component or it is shown without internal components
        if (not self.PARTS or depth == 0) and hasattr(self,"LAYOUT_CONFIG"):
            self.config.update(self.LAYOUT_CONFIG)

        # port_map maintain mapping of (node-id,wire) -> (ELK port-id)
        inner_port_map = {}
        if depth == 0 or not self.PARTS: # just create an IC box
            if 'height' not in self.config:
                # determine component's height from the maximum number of
                # ports on each side
                port_max = max(len(self.IN),len(self.OUT))
                self.config['height'] = port_max * self.config['port_spacing']
            if 'label' not in self.config:
                self.config['label'] = self.name
            box = self._create_body(self.name)
        else:
            children = []
            for i,node in self.nodes.items():
                subcomp_id = f'{base_id}_{i}'
                subcomp,inner_port_map[i] = node.component._generate_elk(depth-1,netmap,subcomp_id)
                subcomp['node_id'] = node.id
                children.append(subcomp)
            # use original label when internal components are shown
            self.config['label'] = self.name
            box = {
                'id' : self.name,
                'children' : children,
                }

        # map a wire to its source port object (wire -> port-id)
        sources = {}  

        # map a wire to one of its destination at node-id to port object
        # ((node-id,wire) -> port-id)
        # node-id is None in case of wire ending up at an external port
        dests = {}

        # add input and output ports to the left and right sides of the
        # component box, respectively;
        # also maintain port_map to be exposed to the outer component
        port_map = {}
        elk_ports = []
        ports = [(w,'in') for w in self.IN[::-1]]
        ports += [(w,'out') for w in self.OUT]
        for i,(wire,dir) in enumerate(ports):
            #port_id = f'{base_id}_{i}'
            port_id = f'{self.name}:{wire.name}'
            elk_port = self._create_port(wire,port_id,i,dir)
            # attach wire's name to help styling
            netwire = VisualMixin._generate_net_wiring(self.wiring[wire.get_key()],netmap)
            netwire['name'] = wire.name
            elk_port['wire'] = netwire
            elk_ports.append(elk_port)
            port_map[wire.get_key()] = elk_port['id']
        box['ports'] = elk_ports

        # when internal components are shown, also add edges to represent
        # inner wiring
        if depth > 0 and self.PARTS:
            # collect input pin IDs
            for pin in self.IN:
                sources[pin.get_key()] = port_map[pin.get_key()]

            # collect output pin IDs
            for pin in self.OUT:
                dests[(None,pin.get_key())] = port_map[pin.get_key()]

            # collect internal pin IDs
            for node in self.nodes.values():
                for pin in node.component.IN:
                    wire = node.component.get_actual_wire(pin.name)
                    dests[(node.id,pin.get_key())] = inner_port_map[node.id][pin.get_key()]
                    # if this wire is a constant, also add a source connector for it
                    if wire.is_constant:
                        conn = self._create_constant(
                                wire.get_constant_signal().get(),
                                wire.width,
                                f'{node.component.name}:{pin.name}')
                        sources[wire.get_key()] = conn['ports'][0]['id']
                        box['children'].append(conn)

                for pin in node.component.OUT:
                    wire = node.component.get_actual_wire(pin.name)
                    sources[wire.get_key()] = inner_port_map[node.id][pin.get_key()]

            edges = []

            # add incoming wires to all subcomponents,
            # except bus wires and constant wires
            for node in self.nodes.values():
                for pin,wire in node.in_dict.items():
                    wire_obj = node.in_wires[pin]
                    if wire_obj.width > 1:  # skip bus wire
                        continue
                    start = sources[wire]
                    end = dests[(node.id,pin)]
                    edge = self._create_edge(start,end)
                    # attach wire's name to help styling
                    netwire = VisualMixin._generate_net_wiring(node.component.wiring[pin],netmap)
                    netwire['name'] = node.in_wires[pin].name
                    edge['wire'] = netwire
                    edges.append(edge)

            # output to outer ports are not yet wired; take care of them
            # also skip bus wires
            for pin in self.OUT:
                if pin.width > 1:
                    continue
                wire = pin.get_key()
                start = sources[wire]
                end = dests[(None,wire)]
                edge = self._create_edge(start,end)
                # attach wire's name to help styling
                netwire = VisualMixin._generate_net_wiring(self.wiring[pin.get_key()],netmap)
                netwire['name'] = pin.name
                edge['wire'] = netwire
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
    def _resolve_dependencies(self):
        unexplored = [self.__class__]
        resolved = []
        resolved_set = set()
        while unexplored:
            comp = unexplored[-1]
            if comp in resolved_set: # it may have already been resolved
                unexplored.pop()
                continue
            deps = set(c.__class__ for c in comp.PARTS
                                   if c.__class__ not in resolved_set)
            if deps:
                unexplored.extend(deps)
            else:  # comp's dependencies already resolved
                resolved.append(comp)
                resolved_set.add(comp)
                unexplored.pop()
        return resolved

    ################
    @classmethod
    def _generate_part_config(cls):
        name = cls.__name__
        inputs = ','.join([f'"{w.name}"' for w in cls.IN])
        outputs = ','.join([f'"{w.name}"' for w in cls.OUT])
        if cls.PARTS:
            return COMPOUND_GATE_JS_TEMPLATE.format(
                name=name,
                inputs=inputs,
                outputs=outputs,
            )
        else:
            process = [PROCESS_JS_TEMPLATE.format(pin=k,function=v)
                        for k,v in cls.process.js.items()]
            return PRIMITIVE_GATE_JS_TEMPLATE.format(
                name=name,
                inputs=inputs,
                outputs=outputs,
                process='\n'.join(process),
            )

    ################
    def generate_elk(self,depth=0,**kwargs):
        layout,port_map = self._generate_elk(depth,self.netmap,**kwargs)

        connectors = []
        conlinks = []
        ports = [(p,'in') for p in self.IN[::-1]]
        ports += [(p,'out') for p in self.OUT]
        for i,(port,dir) in enumerate(ports):
            netwire = VisualMixin._generate_net_wiring(
                    self.wiring[port.get_key()],self.netmap)
            netwire['name'] = port.name
            connector = self._create_connector(f'{self.name}:{port.name}',dir,port.width)
            connector['wire'] = netwire
            connectors.append(connector)
            connector_id = connector['ports'][0]['id']
            port_id = port_map[port.get_key()]
            conlink = self._create_edge(connector_id,port_id)
            conlink['id'] = f'CE_{i}'
            conlink['wire'] = netwire
            conlinks.append(conlink)

        return {
            'id' : 'root',
            'children' : [layout] + connectors,
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
    @staticmethod
    def _generate_net_wiring(net_wiring,netmap):
        net,nslice = net_wiring
        start,stop,_ = nslice.indices(net.width)
        if (start,stop) == (0,1): # single wire; omit slicing
            return {
                'net' : netmap[net],
            }
        else:
            return {
                'net' : netmap[net],
                'slice' : [stop-1,start],
            }

    ################
    @staticmethod
    def _generate_wiring(comp,netmap):
        wiring = {}
        for w in comp.IN + comp.OUT:
            wiring[w.name] = VisualMixin._generate_net_wiring(
                    comp.wiring[w.get_key()],netmap)
        return wiring

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
            wiring = VisualMixin._generate_wiring(comp,self.netmap)
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
                        'slice' : [stop-1,start],
                    })
            nets.append({
                'name' : net.name,
                'width' : net.width,
                'signal' : net.signal.get(),
                'sources' : sources,
                'wiring' : VisualMixin._generate_wiring(comp,self.netmap),
            })

        # combine all configs
        config = {
            'parts': parts,
            'nets': nets,
        }
        return config

    ################
    def generate_js(self,indent=None,depth=0,**kwargs):
        self.flatten()
        lines = []

        # main component configuration
        comp_js = json.dumps(self._generate_component_config(),indent=indent)
        lines.append('var comp_config = ' + comp_js + ';')

        # main component's wiring and all used primitives
        used_primitives = set(p.__class__ for p in self.primitives)
        part_configs_js = ','.join(p._generate_part_config()
                for p in [self.__class__]+list(used_primitives))
        lines.append('')
        lines.append('comp_config.part_configs = {' + part_configs_js + '\n};')

        # instantiate the main component
        lines.append('')
        lines.append('var component = new Component(comp_config);')

        # ELK graph
        lines.append('')
        elk = self.generate_elk(depth,**kwargs)
        lines.append('var graph = '
                + json.dumps(elk,indent=indent)
                + ';')

        ## create mapping from ELK's node id to corresponding component
        #lines.append('')
        #lines.append('var node_map = {}')
        #node_map = {}
        #self._generate_node_map(elk['children'][0],node_map,'component')
        ## create the mapping for the root component manually
        #node_map[elk['children'][0]['id']] = 'component'
        #node_map['root'] = 'component'

        #for k,v in node_map.items():
        #    lines.append(f'node_map.{k} = {v}')

        lines.append('')
        lines.append('var config = {component: component, graph: graph};');

        return '\n'.join(lines)

    
def interact(component_class,**kwargs):
    import IPython.display as DISP

    DISP.display_html(DISP.HTML("""
        <script src="https://d3js.org/d3.v5.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/elkjs@0.6.2/lib/elk.bundled.js"></script>
        <script src="https://www.cpe.ku.ac.th/~cpj/tmp/component.js"></script>
        <script src="https://www.cpe.ku.ac.th/~cpj/tmp/visual.js"></script>
    """))
    DISP.display_html(
        DISP.HTML('<script>' + component_class().generate_js(**kwargs) + '</script>'))
    DISP.display_html(DISP.HTML("""
        <link rel="stylesheet" type="text/css" href="https://www.cpe.ku.ac.th/~cpj/tmp/styles.css" />
        <div id="diagram"></div>
        <script>
          compbuilder.create("#diagram",config);
        </script>
    """))

from copy import deepcopy
from textwrap import dedent
import json

DEFAULT_LAYOUT_CONFIG = {
    'width' : 60,
    'port_spacing' : 20,
    'label_width' : 50,
    'label_height' : 10,
    'port_width' : 8,
    'port_height' : 8,
    'connector_width' : 20,
    'connector_height' : 12,
}

COMPONENT_JS = """
///////////////////////////////////////////////////
var Component = function(config) {
  this.config = config;
  this.wires = {};
  this.initialize();
};

///////////////////////////////////////////////////
Component.SIGPAT = /^([A-Za-z_]\w*)(\[(\d+)(:(\d+))?\])?$/;
Component.parse_signal = function(signal) {
  // > Component.parse_signal('w')
  // { name: 'w', start: 0, end: 0 }
  // > Component.parse_signal('w[8:3]')
  // { name: 'w', start: 8, end: 3 }
  // > Component.parse_signal('output[0]')
  // { name: 'output', start: 0, end: 0 }
  // > Component.parse_signal('output[1]')
  // { name: 'output', start: 1, end: 1 }
  var m = Component.SIGPAT.exec(signal);
  var name = m[1];
  var start = m[3];
  var end = m[5];
  if (start)
    end = end || start;
  else {
    start = 0;
    end = 0;
  }
  return {name:name, start:parseInt(start), end:parseInt(end)};
};

///////////////////////////////////////////////////
Component.prototype.initialize = function() {
  // recursively instantiate all of the component's parts based on their
  // configurations
  this.parts = {};
  this.topo_ordering = [];
  if (this.config.parts) {
    for (var p of this.config.parts) {
      var inner_comp = new Component(p.config);
      inner_comp.initialize();
      inner_comp.id = p.id;
      inner_comp.wiring = p.wiring;
      this.topo_ordering.push(p.id);
      this.parts[p.id] = inner_comp;
    }
  }
};

///////////////////////////////////////////////////
Component.prototype.set_signal = function(signal,value) {
  var sig = Component.parse_signal(signal);
  var mask = (1 << (sig.start-sig.end+1)) - 1;
  value = (value & mask) << sig.end;
  var newval = this.wires[sig.name] || 0;
  // enforce unsigned with >>> operator
  this.wires[sig.name] = ((newval & ~(mask << sig.end)) | value) >>> 0;
  return this;
};

///////////////////////////////////////////////////
Component.prototype.get_signal = function(signal) {
  var sig = Component.parse_signal(signal);
  var value = this.wires[sig.name];
  if (value == undefined)
    throw "Undefined signal value";
  var mask = (1 << (sig.start-sig.end+1)) - 1;
  // enforce unsigned with >>> operator
  return ((value >> sig.end) & mask) >>> 0;
};

///////////////////////////////////////////////////
Component.prototype.process = function(inputs) {
  // populate input wires
  for (var k in inputs) {
    this.wires[k] = inputs[k];
  }

  // use component's own process when available
  if (this.config.process) {
    for (var output of this.config.outputs) {
      var value = this.config.process[output](inputs);
      this.set_signal(output,value);
    }
  }
  else { // otherwise, call each internal component one by one
    for (var id of this.topo_ordering) {
      var p = this.parts[id];
      // assign input values for the inner part p from the incoming wires
      for (var input of p.config.inputs) {
        var value = this.get_signal(p.wiring[input])
        p.set_signal(input,value);
      }
      p.process(p.wires);
      // assign resulting outputs to outgoing wires
      for (var output of p.config.outputs) {
        this.set_signal(p.wiring[output],p.wires[output]);
      }
    }
  }
}
"""

GATE_JS_TEMPLATE = dedent('''
  GATES.{name} = {{
    name: "{name}",
    inputs: [{inputs}],
    outputs: [{outputs}],
    parts: [ // must be topologically sorted
  {parts}
    ]
  }};''')

PRIMITIVE_GATE_JS_TEMPLATE = dedent('''
  GATES.{name} = {{
    name: "{name}",
    inputs: [{inputs}],
    outputs: [{outputs}],
    parts: [],
    process: {{
  {process}
    }}
  }};''')

PART_JS_TEMPLATE = ' '*4 + '{{ id: {id}, config: GATES.{name}, wiring: {{{wiring}}} }},'
PROCESS_JS_TEMPLATE = ' '*4 + '"{pin}" : function(w) {{ {statement} }},'
NEW_COMPONENT_JS_TEMPLATE = dedent('''
  var component = new Component(GATES.{name});
  component.process({{{inputs}}});
''')

################################
class VisualMixin:

    ################
    def _create_body(self,comp_id):
        body = {
            'id' : f'N{comp_id}',
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
    def _create_port(self,name,port_id,index,type):
        side = {'in': 'WEST','out':'EAST'}[type]
        port = {
            'id': f'P{port_id}',
            'properties': {
              'port.side': side,
              'port.index': index,
            },
            'width': self.config['port_width'],
            'height': self.config['port_height'],
        }
        try:  # use configured port label if available
            label = self.config['ports'][name]['label']
        except KeyError:
            label = name

        if label:
            port['labels'] = [{
                'id' : f'LP{port_id}',
                'text' : label,
                'width' : 6*len(label),
                'height' : self.config['label_height'],
            }]

        return port

    ################
    def _create_connector(self,port_id,dir):
        port_side = {'in':'EAST','out':'WEST'}[dir]
        return {
            'id' : f'C_{port_id}',
            'type' : 'connector',
            'direction' : dir,
            'width' : self.config['connector_width'],
            'height' : self.config['connector_height'],
            'ports' : [{
                'id': f'C{dir[0].upper()}_{port_id}',
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
    def _create_edge(self,src,dst):
        return { 'sources' : [src], "targets" : [dst] }

    ################
    def _generate_elk(self,depth,base_id=''):
        # instantiate the component class so that we can work with
        # subcomponent graph
        if self.graph is None:
            self.initialize()

        self.config = deepcopy(DEFAULT_LAYOUT_CONFIG)
        if hasattr(self,"LAYOUT_CONFIG"):
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
                self.config['label'] = self.get_gate_name()
            box = self._create_body(base_id)
        else:
            children = []
            for i,node in self.graph['nodes'].items():
                subcomp_id = f'{base_id}_{i}'
                subcomp,inner_port_map[i] = node.component._generate_elk(depth-1,subcomp_id)
                subcomp['node_id'] = node.id
                children.append(subcomp)
            # use original label when internal components are shown
            self.config['label'] = self.get_gate_name()
            box = {
                'id' : f'N{base_id}',
                'children' : children,
                }

        # positions of signals' sources (wire -> port-id)
        sources = {}  

        # positions of signals' destinations ((node-id,wire) -> port-id)
        # node-id is None in case of wire ending up at an external port
        dests = {}

        # add input and output ports to the left and right sides of the
        # component box, respectively;
        # also maintain port_map to be exposed to the outer component
        port_map = {}
        elk_ports = []
        ports = [(p,'in') for p in self.IN[::-1]]
        ports += [(p,'out') for p in self.OUT]
        for i,(port,type) in enumerate(ports):
            port_id = f'{base_id}_{i}'
            elk_port = self._create_port(port.name,port_id,i,type)
            # attach wire's name to help styling
            elk_port['wire'] = port.name
            elk_ports.append(elk_port)
            port_map[port.get_key()] = elk_port['id']
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
            for node in self.graph['nodes'].values():
                for pin in node.component.IN:
                    wire = node.component.get_actual_edge(pin.name)
                    dests[(node.id,pin.get_key())] = inner_port_map[node.id][pin.get_key()]

                for pin in node.component.OUT:
                    wire = node.component.get_actual_edge(pin.name)
                    sources[wire.get_key()] = inner_port_map[node.id][pin.get_key()]

            edges = []

            # add incoming wires to all subcomponents
            for node in self.graph['nodes'].values():
                for pin,wire in node.in_dict.items():
                    start = sources[wire]
                    end = dests[(node.id,pin)]
                    edge = self._create_edge(start,end)
                    # attach wire's name to help styling
                    edge['wire'] = node.in_wires[pin].name
                    edges.append(edge)

            # output to outer ports are not yet wired; take care of them
            for pin in self.OUT:
                wire = pin.get_key()
                start = sources[wire]
                end = dests[(None,wire)]
                edge = self._create_edge(start,end)
                # attach wire's name to help styling
                edge['wire'] = pin.name
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
    def _generate_gate_config_js(self):
        name = self.__class__.__name__
        inputs = ','.join([f'"{w.name}"' for w in self.IN])
        outputs = ','.join([f'"{w.name}"' for w in self.OUT])
        if self.graph is None:
            self.initialize()
        if self.PARTS:  # compound component
            parts = []
            for node in self.topo_ordering:
                component = node.component
                wires = component.wire_assignments
                wstr = ','.join(f'"{k}":"{v.name}"' for k,v in wires.items())
                parts.append(PART_JS_TEMPLATE.format(
                    id=node.id,
                    name=component.__class__.__name__,
                    wiring=wstr,
                ))
            return GATE_JS_TEMPLATE.format(
                name=name,
                inputs=inputs,
                outputs=outputs,
                parts='\n'.join(parts),
            )
        else: # primitive component
            process = [PROCESS_JS_TEMPLATE.format(pin=k,statement=v)
                        for k,v in self.process.js.items()]
            return PRIMITIVE_GATE_JS_TEMPLATE.format(
                name=name,
                inputs=inputs,
                outputs=outputs,
                process='\n'.join(process),
            )

    ################
    def generate_elk(self,depth=0,**kwargs):
        layout,port_map = self._generate_elk(depth,**kwargs)

        connectors = []
        conlinks = []
        ports = [(p,'in') for p in self.IN[::-1]]
        ports += [(p,'out') for p in self.OUT]
        for i,(port,dir) in enumerate(ports):
            connector = self._create_connector(i,dir)
            connector['wire'] = port.name
            connectors.append(connector)
            connector_id = connector['ports'][0]['id']
            port_id = port_map[port.get_key()]
            conlink = self._create_edge(connector_id,port_id)
            conlink['id'] = f'CE_{i}'
            conlink['wire'] = port.name
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
    def generate_js(self,indent=None,depth=0,**kwargs):
        gates = self._resolve_dependencies()
        lines = [COMPONENT_JS, 'var GATES = {}']
        for g in gates:
            lines.append(g()._generate_gate_config_js())
        lines.append(NEW_COMPONENT_JS_TEMPLATE.format(
            name=self.__class__.__name__,
            inputs=','.join(f"{w.name}:0" for w in self.IN),
        ))
        elk = self.generate_elk(depth,**kwargs)
        lines.append('var graph = {}'.format(
            json.dumps(elk,indent=indent)))

        # create mapping from ELK's node id to corresponding component
        lines.append('')
        lines.append('var node_map = {}')
        node_map = {}
        self._generate_node_map(elk['children'][0],node_map,'component')
        # create the mapping for the root component manually
        node_map[elk['children'][0]['id']] = 'component'
        node_map['root'] = 'component'

        for k,v in node_map.items():
            lines.append(f'node_map.{k} = {v}')

        lines.append('')
        lines.append('var config = {component: component, graph: graph, node_map: node_map};');

        return '\n'.join(lines)

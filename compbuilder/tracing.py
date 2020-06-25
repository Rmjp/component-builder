from . import Component, Signal, Wire, WireFactory

def assign_internal_component_names(component, suffix='', level=1):
    if not component.internal_components:
        return

    counter = 0
    for c in component.internal_components:
        counter += 1
        this_suffix = '{}-{}'.format(suffix,counter)
        c.component_name= '{}{}'.format(c.get_gate_name(),
                                        this_suffix)
        if level > 1:
            assign_internal_component_names(c,
                                            this_suffix,
                                            level-1)

def extract_parts_with_depth(component, level=1):

    def recurse(component, depth, level, output):
        output.append((depth, component))

        if (level > 1) and (component.internal_components):
                
            for c in component.internal_components:
                recurse(c, depth+1, level-1, output)

    parts = []
    recurse(component, 0, level+1, parts)
    return parts

def init_component_part_names(component, level=1):
    component.initialize()
    assign_internal_component_names(component, level=level)
    component.component_name = component.get_gate_name()
            
def report_parts(component, level=1):
    init_component_part_names(component, level)
    parts = extract_parts_with_depth(component, level)
    return '\n'.join(['{}{}'.format('  ' * d,
                                    c.component_name) for (d,c) in parts])

def trace(component, input_signals, probes, step=None, level=None):
    def check_steps(input_signals, step):
        if input_signals == {}:
            if step == None:
                raise Exception("No simulation steps given")
        
        signal_lengths = [len(x) for x in input_signals.values()]
        if min(signal_lengths) != max(signal_lengths):
            raise Exception("Input signals must have identical length")

        if (step != None) and signal_lengths != step:
            raise Exception("Simulation steps mismatch")

    check_steps(input_signals, step)
        
    component.initialize()
    component_wire_map = {w.name:w
                          for w in component.IN + component.OUT}

    if level == None:  # only top level trace
        trace_wire_map = {name:(component,component_wire_map[name])
                          for name in component_wire_map}
    else:
        init_component_part_names(component, level)
        trace_wire_map = {}

        for d,c in extract_parts_with_depth(component, level):
            trace_wire_map.update({(c.component_name + ':' + w.name):(c,w)
                                   for w in c.IN + c.OUT})

    if input_signals == {}:
        input_signals = {'dummysignalorhfiusgrewrgltewr':'0' * step}
            
    outs = []
    out_names = [x.name for x in component.OUT]
    for bits in zip(*input_signals.values()):
        ins = {name:Signal(int(signal),component_wire_map[name].width)
               for name,signal in zip(input_signals.keys(),bits)}
        out_signals = component.eval(**ins)

        res = {}
        for name in trace_wire_map:
            res[name] = trace_wire_map[name][0].trace_signals[trace_wire_map[name][1].name]
        outs.append(res)

        
    print(outs)
    

from . import Component, Signal, Wire, WireFactory

from .myhdlpeek_wavedrom import wavejson_to_wavedrom

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
            return
        
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
        input_signals = {'dummy_signal_orhfiusgrewrgltewr':'0' * step}
            
    outs = {probe:[] for probe in probes}
    for bits in zip(*input_signals.values()):
        ins = {name:Signal(int(signal),component_wire_map[name].width)
               for name,signal in zip(input_signals.keys(),bits)}
        out_signals = component.eval(**ins)

        res = {}
        extracted_trace_cids = set()
        
        for name in outs:
            c = trace_wire_map[name][0]
            cid = c.cid
            if cid not in extracted_trace_cids:
                component.extract_component_trace(c)
                extracted_trace_cids.add(cid)

            out_signal = c.trace_signals[trace_wire_map[name][1].name]
            outs[name].append(Signal(out_signal.value, out_signal.width))

    output = {}
    for probe in probes:
        wire = trace_wire_map[probe][1]
        if wire.width == 1:
            output[probe] = ''.join([str(s.value) for s in outs[probe]])
        else:
            output[probe] = outs[probe]

    return output

def make_wavejson_entry(name,signal):
    if isinstance(signal,str): # 1-bit signal
        # suppress duplicate consecutive bits
        result = []
        prev = None
        for x in signal:
            result.append(x if x != prev else '.')
            prev = x
        return {'name':name, 'wave':''.join(result)}
    else: # bus signal
        return {'name':name,
                'wave':'='*len(signal),
                'data':[f'0x{s:X}' for s in signal]}

def wavejsonify(signal_groups):
    """Constructs a WaveJSON to be used by WaveDrom.  In addition, consecutive
    bit symbols 0 and 1 are converted into '.' to remove spikes in the
    visualization."""

    all_signals = []
    for label in signal_groups:
        signals = signal_groups[label]
        waves = [make_wavejson_entry(k,v) for k,v in signals.items()]
        all_signals.append([label, *waves])
        all_signals.append({})

    del all_signals[-1]
    
    return {'signal': all_signals}

def wavejsonify_inout(inputs, outputs):
    return wavejsonify({'Input':inputs,
                        'Output':outputs})


def plot_trace_inout(inputs, outputs):
    wavejson_to_wavedrom(wavejsonify_inout(inputs, outputs))

def plot_trace(signal_groups):
    wavejson_to_wavedrom(wavejsonify(signal_groups))


def trace_and_plot_inout(component, input_signals, probes=None, step=None, level=None):
    if not probes:
        probes = [w.name for w in component.OUT]

    output_signals = trace(component, input_signals, probes, step, level)
    plot_trace_inout(input_signals, output_signals)


def trace_and_plot(component, input_signals, signal_label_groups, step=None, level=None):
    probes = []
    for names in signal_label_groups.values():
        probes += names

    out_signals = trace(component, input_signals, probes, step, level)

    signal_groups = {}
    for label in signal_label_groups:
        signal_groups[label] = {name:out_signals[name] 
                                for name in signal_label_groups[label]}
            
    plot_trace(signal_groups)



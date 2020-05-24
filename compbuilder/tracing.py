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

def extract_parts(component, level=1):

    def recurse(component, depth, level, output):
        output.append((depth, component))

        if (level > 1) and (component.internal_components):
                
            for c in component.internal_components:
                recurse(c, depth+1, level-1, output)

    parts = []
    recurse(component, 0, level+1, parts)
    return parts
    
            
def report_parts(component, level=1):
    component.initialize()
    assign_internal_component_names(component, level=level)
    component.component_name = component.get_gate_name()

    parts = extract_parts(component, level)
    return '\n'.join(['{}{}'.format('  ' * d,
                                    c.component_name) for (d,c) in parts])
            

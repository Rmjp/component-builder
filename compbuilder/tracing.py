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
        
def report_parts(component, level=1):

    def recurse(component, indent, level, output):
        output.append('{}{}'.format('  ' * indent,
                                    component.component_name))

        if (level > 1) and (component.internal_components):
                
            for c in component.internal_components:
                recurse(c, indent+1, level-1, output)
    
    if not component.internal_components:
        component.build_graph()
        
    assign_internal_component_names(component, level=level)
    component.component_name = component.get_gate_name()

    output = []
    recurse(component, 0, level+1, output)
    return '\n'.join(output)
            

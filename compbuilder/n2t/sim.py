def simulate(instructions, memory_display_slots=30, screen_scale=1, light_weight=False, fastest_steps=103, super_fast=False):
    import IPython.display as DISP

    if (len(instructions) > 0) and (type(instructions[0]) == str):
        load_instructions = 'simulator.loadInstructions([' + ','.join([str(int(inst, 2)) for inst in instructions]) + ']);'
    else:
        load_instructions = 'simulator.loadInstructions([' + ','.join([str(inst) for inst in instructions]) + ']);'

    if super_fast:
        if not light_weight:
            light_weight = True
        if fastest_steps < 5003:
            fastest_steps = 5003

    if light_weight:
        mem_callback_comments = '//'
    else:
        mem_callback_comments = ''
    
    DISP.display_html(DISP.HTML('''
<link rel="stylesheet" href="https://jittat.gitlab.io/hacksim/sim.css">
<div id="sim-ui">
  <simulator v-bind:simulator="simulator" memory-display-slots="''' + str(memory_display_slots) + '''" screen-scale="''' + str(screen_scale) + '''" v-bind:light-weight="''' + str(light_weight).lower() + '''" fastest-steps="''' + str(fastest_steps) + '''"/>
</div>
<script>var exports = {};</script>
<script src="https://cdn.jsdelivr.net/npm/vue/dist/vue.js"></script>
<script src="https://jittat.gitlab.io/hacksim/simulator.js"></script>
<script src="https://jittat.gitlab.io/hacksim/simulator-ui.js"></script>
<script>
  var simulator = new HackSimulator();
''' + load_instructions + '''
  ''' + mem_callback_comments + '''simulator.memoryWriteCallbacks.push(memUpdateCallback);
  simulator.memoryWriteCallbacks.push(screenUpdateCallback);

  var app = new Vue({
    el: '#sim-ui',
    data: {
      simulator: simulator
    }
  });
</script>
'''))

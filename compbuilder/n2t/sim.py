def simulate(instructions, memory_display_slots=30, screen_scale=1):
    import IPython.display as DISP

    load_instructions = 'simulator.loadInstructions([' + ','.join([str(inst) for inst in instructions]) + ']);'

    DISP.display_html(DISP.HTML('''
<link rel="stylesheet" href="https://jittat.gitlab.io/hacksim/sim.css">
<div id="sim-ui">
  <simulator v-bind:simulator="simulator" memory-display-slots="''' + str(memory_display_slots) + '''" screen-scale="''' + str(screen_scale) + '''"/>
</div>
<script>var exports = {};</script>
<script src="https://cdn.jsdelivr.net/npm/vue/dist/vue.js"></script>
<script src="https://jittat.gitlab.io/hacksim/simulator.js"></script>
<script src="https://jittat.gitlab.io/hacksim/simulator-ui.js"></script>
<script>
  var simulator = new HackSimulator();
''' + load_instructions + '''
  simulator.memoryWriteCallbacks.push(memUpdateCallback);
  simulator.memoryWriteCallbacks.push(screenUpdateCallback);

  var app = new Vue({
    el: '#sim-ui',
    data: {
      simulator: simulator
    }
  });
</script>
'''))

///////////////////////////////////////////////////
var Component = function(comp_config) {
  for (var k in comp_config) {
    this[k] = comp_config[k];
  }

  // resolve references to nets, components, primitives, etc.
  for (var w in this.wiring) {
    var net_idx = this.wiring[w].net;
    this.wiring[w].net = this.nets[net_idx];
  }
  for (var p of this.parts) {
    p.config = this.part_configs[p.config];
    for (var w in p.wiring) {
      var net_idx = p.wiring[w].net;
      p.wiring[w].net = this.nets[net_idx];
    }
  }
  for (var n of this.nets) {
    for (var source of n.sources) {
      source.part = this.parts[source.part];
    }
  }

  // give parts their own states
  for (var p of this.parts) {
    p.states = {};
  }
};

///////////////////////////////////////////////////
Component.prototype.set_net_signal = function(net,slice,value) {
  var slice = slice || [0,0];
  var mask = (1 << (slice[0]-slice[1]+1)) - 1;
  value = (value & mask) << slice[1];
  var newval = net.signal || 0;
  // enforce unsigned with >>> operator
  net.signal = ((newval & ~(mask << slice[1])) | value) >>> 0;
};

///////////////////////////////////////////////////
Component.prototype.get_net_signal = function(net,slice) {
  var slice = slice || [0,0];
  var signal = net.signal;
  if (signal == undefined)
    throw "Undefined signal value";
  var mask = (1 << (slice[0]-slice[1]+1)) - 1;
  // enforce unsigned with >>> operator
  return ((signal >> slice[1]) & mask) >>> 0;
};

///////////////////////////////////////////////////
Component.prototype.trigger = function(part) {
  // Trigger this primitive part by processing values from input nets and
  // store results in output nets.
  var inputs = {};
  for (var win of part.config.IN) {
    var wiring = part.wiring[win];
    inputs[win] = this.get_net_signal(wiring.net, wiring.slice);
  }
  for (var wout of part.config.OUT) {
    var wiring = part.wiring[wout];
    var signal = part.config.process[wout](inputs,part.states);
    this.set_net_signal(wiring.net,wiring.slice,signal);
  }
};

///////////////////////////////////////////////////
Component.prototype.update = function(inputs) {
  var comp = this.parts[0]; // the first part is the main component

  // populate input nets
  for (var w in inputs) {
    var wiring = comp.wiring[w];
    this.set_net_signal(wiring.net,wiring.slice,inputs[w]);
  }

  // populate the remaining nets by their topological ordering
  // (netlist must have already been topologically sorted)
  for (var net of this.nets) {
    for (source of net.sources) {
      if (source.part != comp) // do not trigger the main component
        this.trigger(source.part);
    }
  }

  // extract the outputs
  var outputs = {};
  for (var w of comp.config.OUT) {
    var wiring = comp.wiring[w];
    outputs[w] = this.get_net_signal(wiring.net,wiring.slice);
  }
  return outputs;
};

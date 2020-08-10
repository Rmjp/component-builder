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
    n.transient_signal = 0;
    for (var source of n.sources) {
      source.part = this.parts[source.part];
    }
  }

  // give parts their own states
  for (var p of this.parts) {
    p.states = {};
    if (p.config.init) {
      p.config.init(p.states);
    }
  }
};

///////////////////////////////////////////////////
Component.prototype.set_net_signal = function(net,slice,value,trans) {
  var slice = slice || [net.width-1,0];
  var mask = (1 << (slice[0]-slice[1]+1)) - 1;
  value = (value & mask) << slice[1];
  if (!trans) {
    var newval = net.signal || 0;
    // enforce unsigned with >>> operator
    net.signal = ((newval & ~(mask << slice[1])) | value) >>> 0;
  }
  else {
    var newval = net.transient_signal || 0;
    // enforce unsigned with >>> operator
    net.transient_signal = ((newval & ~(mask << slice[1])) | value) >>> 0;
  }
};

///////////////////////////////////////////////////
Component.prototype.get_net_signal = function(net,slice,trans) {
  var slice = slice || [net.width-1,0];
  var signal = trans ? net.transient_signal : net.signal;
  if (signal == undefined)
    throw "Undefined signal value";
  var mask = (1 << (slice[0]-slice[1]+1)) - 1;
  // enforce unsigned with >>> operator
  return ((signal >> slice[1]) & mask) >>> 0;
};

///////////////////////////////////////////////////
Component.prototype.trigger = function(part) {
  // Trigger this primitive part by processing values from input nets and
  // store results in output nets.  To avoid race conditions, the trigger
  // process stores results in transient net signals (which must have already
  // been prepared).  The new signals must later on be copied over the current
  // signals before triggering the components attached to the nets in the next
  // topological level.  Return a set of affected nets.
  var inputs = {};
  var affected = new Set();
  for (var win of part.config.IN) {
    var wiring = part.wiring[win];
    inputs[win] = this.get_net_signal(wiring.net, wiring.slice);
  }
  for (var wout of part.config.OUT) {
    if (!part.config.process[wout])
      continue; // no process defined for this output
    var wiring = part.wiring[wout];
    var signal = part.config.process[wout](inputs,part.states);
    this.set_net_signal(wiring.net,wiring.slice,signal,true);
    affected.add(wiring.net);
  }

  // in case the part is associated with a GUI widget, call the widget's
  // trigger function, if available
  if (part.widget && part.widget.trigger) {
    part.widget.trigger(inputs,part.states);
  }

  return affected;
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
  var current_level = 0;
  var transient_nets = new Set();
  for (var net of this.nets) {
    if (net.level != current_level) {
      // new level -- update previous-level nets with their transient
      // signals
      for (var tnet of transient_nets) {
        tnet.signal = tnet.transient_signal;
      }
      transient_nets.clear();
      current_level = net.level;
    }
    for (var source of net.sources) {
      if (source.part != comp) { // do not trigger the main component
        var affected = this.trigger(source.part);
        for (var a of affected) {
          transient_nets.add(a);
        }
      }
    }
  }
  // update from the transient signals in the final level
  for (var tnet of transient_nets) {
    tnet.signal = tnet.transient_signal;
  }

  // extract the outputs
  var outputs = {};
  for (var w of comp.config.OUT) {
    var wiring = comp.wiring[w];
    outputs[w] = this.get_net_signal(wiring.net,wiring.slice);
  }
  return outputs;
};

///////////////////////////////////////////////////
var Component = function(compConfig) {
  for (var k in compConfig) {
    this[k] = compConfig[k];
  }

  // resolve references to nets, components, primitives, etc.
  for (var w in this.wiring) {
    var netIdx = this.wiring[w].net;
    this.wiring[w].net = this.nets[netIdx];
  }
  for (var p of this.parts) {
    p.config = this.partConfigs[p.config];
    for (var w in p.wiring) {
      var netIdx = p.wiring[w].net;
      p.wiring[w].net = this.nets[netIdx];
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
Component.prototype.setNetSignal = function(net,slice,value,trans) {
  var slice = slice || [0,net.width-1];
  var mask = (1 << (slice[1]-slice[0]+1)) - 1;
  value = (value & mask) << slice[0];
  if (!trans) {
    var newval = net.signal || 0;
    // enforce unsigned with >>> operator
    net.signal = ((newval & ~(mask << slice[0])) | value) >>> 0;
  }
  else {
    var newval = net.transient_signal || 0;
    // enforce unsigned with >>> operator
    net.transient_signal = ((newval & ~(mask << slice[0])) | value) >>> 0;
  }
};

///////////////////////////////////////////////////
Component.prototype.getNetSignal = function(net,slice,trans) {
  var slice = slice || [0,net.width-1];
  var signal = trans ? net.transient_signal : net.signal;
  if (signal == undefined)
    throw "Undefined signal value";
  var mask = (1 << (slice[1]-slice[0]+1)) - 1;
  // enforce unsigned with >>> operator
  return ((signal >> slice[0]) & mask) >>> 0;
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
    inputs[win] = this.getNetSignal(wiring.net, wiring.slice);
  }
  for (var wout of part.config.OUT) {
    if (!part.config.process[wout])
      continue; // no process defined for this output
    var wiring = part.wiring[wout];
    var signal = part.config.process[wout](inputs,part.states);
    this.setNetSignal(wiring.net,wiring.slice,signal,true);
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
    this.setNetSignal(wiring.net,wiring.slice,inputs[w]);
  }

  // populate the remaining nets by their topological ordering
  // (netlist must have already been topologically sorted)
  var currentLevel = 0;
  var transientNets = new Set();
  for (var net of this.nets) {
    if (net.level != currentLevel) {
      // new level -- update previous-level nets with their transient
      // signals
      for (var tnet of transientNets) {
        tnet.signal = tnet.transient_signal;
      }
      transientNets.clear();
      currentLevel = net.level;
    }
    for (var source of net.sources) {
      if (source.part != comp) { // do not trigger the main component
        var affected = this.trigger(source.part);
        for (var a of affected) {
          transientNets.add(a);
        }
      }
    }
  }
  // update from the transient signals in the final level
  for (var tnet of transientNets) {
    tnet.signal = tnet.transient_signal;
  }

  // extract the outputs
  var outputs = {};
  for (var w of comp.config.OUT) {
    var wiring = comp.wiring[w];
    outputs[w] = this.getNetSignal(wiring.net,wiring.slice);
  }
  return outputs;
};

(function (global, factory) {
typeof exports === 'object' && typeof module !== 'undefined' ? factory(exports) :
typeof define === 'function' && define.amd ? define(['exports'], factory) :
(global = global || self, factory(global.compbuilder = global.compbuilder || {}));
}(this, function (exports) {
'use strict';

// create a dummy canvas context for measuring text width
// (adapted from https://stackoverflow.com/a/35373030)
var context = document.createElement('canvas').getContext('2d');

var DEFAULT_FONT_SIZE = 16*0.8;
var DEFAULT_FONT_FACE = "Arial";

var widgetConfigs = {};
var widgets = [];
var hoveredSignal = null;
var stampedSignals = [];
var component = null;
var msgdiv = null;

//////////////////////////////////
function signalValueHex(value,bits) {
  var digits = Math.ceil(bits/4);
  var s = "000000000" + value.toString(16).toUpperCase(); // left pad with zero
  return s.substr(s.length-digits);
}

//////////////////////////////////
function signalWidth(wire) {
  if (wire.net.width == 1)
    return 1;
  else if (wire.slice)
    return wire.slice[1] - wire.slice[0] + 1;
  else
    return wire.net.width;
}

//////////////////////////////////
function drawConnector(dir,w,h) {
  if (dir == 'in')
    return "M 0,0 h " + (w-6) + " l 6," + h/2 + " l -6," + h/2 + " h -" + (w-6) + " z";
  else
    return "M " + w + ",0 h -" + (w-6) + " l -6," + h/2 + " l 6," + h/2 + " h " + (w-6) + " z";
}

//////////////////////////////////
function measureText(text,fontSize,fontFace) {
  var fontSize = fontSize || DEFAULT_FONT_SIZE;
  var fontFace = fontFace || DEFAULT_FONT_FACE;
  context.font = fontSize + 'px ' + fontFace;
  return { 
    width: context.measureText(text).width,
    height: fontSize
  }
}

//////////////////////////////////
// Traverse the ELK graph and fill in correct label width
function populateLabelWidth(graph) {
  // TODO
}

//////////////////////////////////
function getEdgeName(e) {
  if (e.node.id == graph.id) // don't show root's name
    return e.name;
  else
    return e.node.id + ":" + e.name;
}

//////////////////////////////////
function updateSignalTooltip(siginfo) {
  var sigval = component.getNetSignal(siginfo.net, siginfo.slice);
  var sigwidth = siginfo.slice[1] - siginfo.slice[0] + 1;
  if (sigwidth == 1) // single-bit signal
    var sigvalstr = sigval.toString();
  else
    var sigvalstr = "0x" + signalValueHex(sigval, sigwidth);
  siginfo.tooltip.html("<span class='signal'>" +
    siginfo.name + " = " + sigvalstr + "</span>"
  );
}

//////////////////////////////////
function updateTooltips() {
  if (hoveredSignal)
    updateSignalTooltip(hoveredSignal);
  for (var siginfo of stampedSignals) {
    updateSignalTooltip(siginfo);
  }
}

//////////////////////////////////
function createPath(edge) {
  var pstr = "";
  edge.sections.forEach(function(s) {
    if (edge.dir == "in")
      // TODO replace the magic number 8 with value from the layout config
      pstr += "M " + (s.startPoint.x-8) + " " + s.startPoint.y + " ";
    else
      pstr += "M " + s.startPoint.x + " " + s.startPoint.y + " ";
    if (s.bendPoints) {
      s.bendPoints.forEach(function(b) {
        pstr += "L " + b.x + " " + b.y + " ";
      });
    }
    pstr += "L " + s.endPoint.x + " " + s.endPoint.y + " ";
  });
  return pstr;
}

//////////////////////////////////
function translate(x,y) {
  return "translate(" + x + " " + y + ")";
}

//////////////////////////////////
function drawChildren(svg,node,component) {
  var nodeGroup = svg.selectAll("g.node")
    .data(node.children, function(n) { return n.id; })
  .enter()
    .append("g")
    .attr("class", "node")
    .attr("id", function(n) { return n.id; })
    .attr("transform", function(n) { return translate(n.x,n.y); });

  nodeGroup
    .each(function(n) { // draw node's body
      if (n.widget) { // always use provided widget when available
        n.widget.svg = d3.select(this);
      }
      else if (n.svg) { // then try provided svg
        d3.select(this).html(n.svg);
      }
      else if (n.type == "connector") { // I/O connector
        d3.select(this)
          .append("path")
            .attr("class","connector " + n.direction)
            .classed("single", function(n) {
              return n.wire.net.width == 1;
            })
            .classed("bus", function(n) {
              return n.wire.net.width > 1;
            })
            .attr("d", drawConnector(n.direction,n.width,n.height));
        n.node_id = graph.id; // connectors are only attached to root node
      }
      else if (n.type == "constant") {
        d3.select(this)
          .append("path")
            .attr("class","constant " + n.direction)
            .attr("d", drawConnector(n.direction,n.width,n.height));
      }
      else { // otherwise, just use a normal rectangle
        d3.select(this)
          .append("rect")
          .attr("class", function(n) {
            if (n.type)
              return "node " + n.type;
            else
              return "node";
          })
          .attr("width", function(n) { return n.width; })
          .attr("height", function(n) { return n.height; });
      }
    })
    .each(function(n) {  // draw ports around each node
      var portGroup = svg.append("g");
      portGroup.selectAll("rect.port")
        .data(n.ports, function(p) { return p.id; })
      .enter()
        .append("rect")
        .attr("class","port")
        .attr("x", function(p) { return p.x; })
        .attr("y", function(p) { return p.y; })
        .attr("width", function(p) { return p.width; })
        .attr("height", function(p) { return p.height; })
        .each(function(p) { 
          // for 'connector' node, propagate wire object into ports
          if (p.type == "connector")
            p.wire = n.wire;
        })
        .each(function(p) { // draw port label
          if (p.labels) {
            p.labels.forEach(function(lb) {
              portGroup.append("text")
                 .attr("class","label")
                 .text(lb.text)
                 .attr("x",lb.x + p.x)
                 .attr("y",lb.y + p.y + p.height)
            });
          }
        });
      portGroup.attr("transform", translate(n.x,n.y));
    })
    .each(function(n) {  // draw node labels
      if (n.labels) {
        var labelGroup = svg.append("g");
        var nodeType = n.type ? n.type : "";
        var offx = 0, offy = 0;
        if (nodeType == "connector" || nodeType == 'constant') {
          // XXX lots of magic here
          offx = n.direction == "out" ? 6 : 4;
          offy = -3;
          nodeType += " " + n.direction;
          nodeType += " " + (n.wire.net.width > 1 ? "bus" : "single");
        }
        labelGroup.selectAll("text.label")
          .data(n.labels, function(lbl) { return lbl.id; })
        .enter()
          .append("text")
          .attr("class", "label " + nodeType)
          .attr("x", function(lbl) { return lbl.x + offx; })
          .attr("y", function(lbl) { return lbl.y + lbl.height + offy; })
          .text(function(lbl) { return lbl.text; })
          .each(function(lbl) {
            // attach wire object to connector's label for later update
            lbl.wire = n.wire;
          });
        labelGroup.attr("transform", translate(n.x,n.y));
      }
    });

  // recursively draw node of each child, if available
  node.children.forEach(function(child) {
    if (child.children) {
      drawNode(svg,child,component);
    }
  });
}

//////////////////////////////////
function drawEdges(svg,node,component) {
  svg.selectAll("path.edge")
    .data(node.edges, function(e) { return e.id; })
  .enter()
    .append("path")
    .attr("id",function(e) { return e.id; })
    .attr("class","edge")
    .classed("bus", function(e) {
      return signalWidth(e.wire) > 1;
    })
    .attr("d", createPath)
    .attr("stroke", "black")
    .attr("fill", "none")
    .each(function(e) { // draw junction points
      if (e.junctionPoints) {
        var juncGroup = svg.append("g");
        juncGroup.selectAll("circle.junction")
          .data(e.junctionPoints)
        .enter()
          .append("circle")
          .attr("class", "junction")
          .attr("r", 2)
          .attr("cx", function(j) { return j.x; })
          .attr("cy", function(j) { return j.y; });
      }
    });
}

//////////////////////////////////
function drawNode(svg,node,component) {
  var group = svg.append("g");
  drawChildren(group,node,component);
  drawEdges(group,node,component);
  group.attr("transform", translate(node.x,node.y));
}

//////////////////////////////////
function updateAllWrapper(svg,component) {
  function updateAll() {
    svg.selectAll("path.edge")
      .classed("T", function(e) {
        return signalWidth(e.wire) == 1 &&
               component.getNetSignal(e.wire.net, e.wire.slice);
      });
    svg.selectAll("rect.port")
      .classed("T", function(p) {
        return signalWidth(p.wire) == 1 &&
               component.getNetSignal(p.wire.net, p.wire.slice);
      });
    svg.selectAll("path.connector")
      .classed("T", function(c) {
        return signalWidth(c.wire) == 1 &&
               component.getNetSignal(c.wire.net, c.wire.slice);
      });
    svg.selectAll("text.label.connector.out")
      .text(function(c) {
        var net = c.wire.net;
        return signalValueHex(net.signal,net.width);
      });
    for (var n of widgets) {
      if (n.update) n.update();
    }
    updateTooltips();
  }

  return updateAll;
}

//////////////////////////////////
var signalTooltipDrag = d3.drag().on("drag", function () {
    d3.select(this)
      .style("left", (d3.event.x) + "px")
      .style("top", (d3.event.y) + "px");
  });

//////////////////////////////////
function createSignalTooltip(px, py) {
  var tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("left", px + "px")
        .style("top", py + "px");
  tooltip.call(signalTooltipDrag);
  return tooltip;
}

//////////////////////////////////
function attachEvents(svg,component) {

  svg.selectAll(".connector.in")
    .on("mouseover", function(c) {
      d3.select(this).classed("hover",true);
    })
    .on("mouseout", function(c) {
      d3.select(this).classed("hover",false);
    })
  svg.selectAll(".connector.in.single")
    .on("click", function(c) {
      var signal = c.wire.net.signal;
      signal = signal ? 0 : 1;
      component.update({[c.wire.name]:signal});
      svg.updateAll();
    });
  svg.selectAll("path.edge")
    .on("mouseover", function(e) {
      for (var edge of e.wire.net.edges) {
        var id = 'path#' + edge.id;
        d3.select(id).classed("hover",true);
      }
      var tooltip = createSignalTooltip(d3.event.pageX + 10, d3.event.pageY + 5);
      tooltip.transition()
        .duration(200)
        .style("opacity", .9);
      hoveredSignal = {
        name: getEdgeName(e),
        net: e.wire.net,
        slice: e.wire.slice,
        tooltip: tooltip
      };
      //exports.hoveredSignal = hoveredSignal;
      updateTooltips();
    })
    .on("mouseout", function(e) {
      for (var edge of e.wire.net.edges) {
        var id = 'path#' + edge.id;
        d3.select(id).classed("hover",false);
      }
      hoveredSignal.tooltip.transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
      hoveredSignal = null;
    })
    .on("click", function(e) {
      var tooltip = createSignalTooltip(d3.event.pageX + 10, d3.event.pageY + 5);
      tooltip.transition()
        .duration(200)
        .style("opacity", .9);
      stampedSignals.push({
        name: getEdgeName(e),
        net: e.wire.net,
        slice: e.wire.slice,
        tooltip: tooltip
      });
      tooltip.on("click", function() {
        if (window.getSelection().type != "Range") {
          var elem = d3.select(this).node();
          for (var i=0; i<stampedSignals.length; i++) {
            if (elem == stampedSignals[i].tooltip.node()) {
              d3.select(this).remove();
              stampedSignals.splice(i,1);
              break;
            }
          }
        }
      });
      updateTooltips();
    });
}

//////////////////////////////////
function inputBlurred() {
  var val = parseInt(this.value,16);
  if (isNaN(val)) {
    // restore original value from the corresponding net
    this.value = signalValueHex(this.net.signal,this.net.width);
  }
  else {
    this.component.update({[this.name]:val});
    this.svg.updateAll();
    this.value = signalValueHex(this.net.signal,this.net.width);
  }
}

//////////////////////////////////
function inputKeyPressed() {
  if (event.key == "Enter") {
    this.blur();
  }
}

//////////////////////////////////
function attachInputs(svg,component) {
  var mapping = {};
  // attach input box for each bus input connector
  svg.selectAll(".connector.in.bus")
    .each(function(lbl) {
      var g = d3.select(this.parentNode);
      g.select("text").remove();
      var net = lbl.wire.net;
      var d3Input = g.append("foreignObject")
        .attr("width",lbl.width-6)
        .attr("height",lbl.height)
        .attr("x","1")
        .attr("y","-1")
        .append("xhtml:div")
          .append("xhtml:input")
            .attr("class","bus-input")
            .attr("size",Math.ceil(net.width/4)+1)
            .attr("maxlength",Math.ceil(net.width/4))
            .attr("name",lbl.wire.name)
            .attr("value",signalValueHex(net.signal,net.width));
      var input = d3Input.node();
      input.onkeypress = inputKeyPressed;
      input.onblur = inputBlurred;
      input.net = lbl.wire.net;
      input.component = component;
      input.svg = svg;
      mapping[input.name] = input;
    });

  return mapping;
}

//////////////////////////////////
var Widget = function(widgetConfig) {
  for (var k in widgetConfig) {
    this[k] = widgetConfig[k];
  }
};

//////////////////////////////////
function getWireWrapper(component,wire) {
  function getWireValue() {
    return component.getNetSignal(wire.net,wire.slice);
  }
  return getWireValue;
}

//////////////////////////////////
function setWireWrapper(component,wire) {
  function setWireValue(value) {
    return component.setNetSignal(wire.net,wire.slice,value);
  }
  return setWireValue;
}

//////////////////////////////////
function resolveReferences(component,node,partmap) {
  // resolve references to net and widget instances
  if (node.type == "connector" || node.type == "constant")
    node.wire.net = component.nets[node.wire.net];
  if (node.widget) {
    if (!widgetConfigs[node.widget]) {
      var err = "Widget " + node.widget + " not registered.";
      msgdiv.innerHTML = err;
      throw err;
    }
    node.widget = new Widget(widgetConfigs[node.widget]);
    node.width = node.widget.width;
    node.height = node.widget.height;
    var getPinValueFuncs = {};   // mapping pin -> signal getter function
    var setPinValueFuncs = {};   // mapping pin -> signal setter function
    for (var p of node.ports) {
      getPinValueFuncs[p.name] = getWireWrapper(component,p.wire);
      setPinValueFuncs[p.name] = setWireWrapper(component,p.wire);
    }
    node.widget.getPinValue = getPinValueFuncs;
    node.widget.setPinValue = setPinValueFuncs;
    var part = partmap[node.id];
    if (part) {
      part.widget = node.widget;
      node.widget.part = part;
    }
    widgets.push(node.widget);
  }
  if (node.ports) {
    for (var port of node.ports) {
      if (port.wire) {
        port.wire.net = component.nets[port.wire.net];
      }
    }
  }
  if (node.edges) {
    for (var edge of node.edges) {
      edge.wire.net = component.nets[edge.wire.net];
      edge.node = node;
      var net = edge.wire.net;
      if (!net.hasOwnProperty('edges'))
        net.edges = []
      net.edges.push(edge);
    }
  }
  if (node.children) {
    for (var child of node.children) {
      resolveReferences(component,child,partmap);
    }
  }
}

//////////////////////////////////
function create(selector,config,msgdivid) {
  var elk = new ELK();
  var partmap = {};
  component = config.component;
  msgdiv = document.querySelector(msgdivid);
  for (var part of component.parts) {
    partmap[part.name] = part;
  }
  resolveReferences(component,config.graph,partmap);
  elk.layout(config.graph).then(function(layout) {
    var svg = d3.select(selector).append("svg")
                                   .attr("width", layout.width)
                                   .attr("height", layout.height);
    drawNode(svg,layout,component);
    for (var w of widgets) {
      w.setup(svg);
      w.rootSvg = svg;
      w.component = component;
    }
    attachEvents(svg,component);
    var inputMapping = attachInputs(svg,component);
    component.update();

    if (config.inputScript) {
      for (var input_val of config.inputScript) {
        component.update(input_val);
        for (var pinName in input_val) {
          if (pinName in inputMapping)
            inputMapping[pinName].value = input_val[pinName];
        }
      }
    }

    if (config.probe) {
      var bound = svg.node().getBoundingClientRect();
      for (var p of config.probe) {
        var tooltip = createSignalTooltip(p.x+bound.left, p.y+bound.top);
        stampedSignals.push({
          name: p.name,
          net: component.nets[p.netId],
          slice: p.slice,
          tooltip: tooltip
        });
        tooltip.style("opacity", .9);
      }
    }
    svg.updateAll = updateAllWrapper(svg,component);
    svg.updateAll();
  });
}

//////////////////////////////////
function registerWidget(name,widgetConfig) {
  widgetConfigs[name] = widgetConfig;
}

//////////////////////////////////
exports.create = create;
exports.registerWidget = registerWidget;

}));

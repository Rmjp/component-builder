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

var widget_configs = {};
var widgets = [];
var hovered_edge = null;
var stamped_edges = [];
var component = null;
var msgdiv = null;

//////////////////////////////////
function signal_value_hex(value,bits) {
  var digits = Math.ceil(bits/4);
  var s = "000000000" + value.toString(16).toUpperCase();
  return s.substr(s.length-digits);
}

//////////////////////////////////
function signal_width(wire) {
  if (wire.net.width == 1)
    return 1;
  else if (wire.slice)
    return wire.slice[0] - wire.slice[1] + 1;
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
function update_tooltip(einfo) {
  var sigval = component.get_net_signal(
    einfo.edge.wire.net, einfo.edge.wire.slice);
  einfo.tooltip.html("<span class='signal'>" +
    einfo.edge.name + " = 0x" + sigval.toString(16).toUpperCase() +
    "</span>"
    );
}

//////////////////////////////////
function update_tooltips() {
  if (hovered_edge)
    update_tooltip(hovered_edge);
  for (var einfo of stamped_edges) {
    update_tooltip(einfo);
  }
}

//////////////////////////////////
function createPath(edge) {
  var pstr = "";
  edge.sections.forEach(function(s) {
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
  var node_group = svg.selectAll("g.node")
    .data(node.children, function(n) { return n.id; })
  .enter()
    .append("g")
    .attr("class", "node")
    .attr("id", function(n) { return n.id; })
    .attr("transform", function(n) { return translate(n.x,n.y); });

  node_group
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
        n.node_id = "root"; // connectors are only attached to root node
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
      return signal_width(e.wire) > 1;
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
function update_all_wrapper(svg,component) {
  function update_all() {
    svg.selectAll("path.edge")
      .classed("T", function(e) {
        return signal_width(e.wire) == 1 &&
               component.get_net_signal(e.wire.net, e.wire.slice);
      });
    svg.selectAll("rect.port")
      .classed("T", function(p) {
        return signal_width(p.wire) == 1 &&
               component.get_net_signal(p.wire.net, p.wire.slice);
      });
    svg.selectAll("path.connector")
      .classed("T", function(c) {
        return signal_width(c.wire) == 1 &&
               component.get_net_signal(c.wire.net, c.wire.slice);
      });
    svg.selectAll("text.label.connector.out")
      .text(function(c) {
        var net = c.wire.net;
        return signal_value_hex(net.signal,net.width);
      });
    for (var n of widgets) {
      if (n.update) n.update();
    }
    update_tooltips();
  }

  return update_all;
}

//////////////////////////////////
var tooltip_drag = d3.drag().on("drag", function () {
    d3.select(this)
      .style("left", (d3.event.x) + "px")
      .style("top", (d3.event.y) + "px");
  });

//////////////////////////////////
function attach_events(svg,component) {

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
      svg.update_all();
    });
  svg.selectAll("path.edge")
    .on("mouseover", function(e) {
      for (var edge of e.wire.net.edges) {
        var id = 'path#' + edge.id;
        d3.select(id).classed("hover",true);
      }
      var tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("left", (d3.event.pageX + 10) + "px")
        .style("top", (d3.event.pageY + 5) + "px");

      tooltip.transition()
        .duration(200)
        .style("opacity", .9);
      hovered_edge = { edge: e, tooltip: tooltip };
      update_tooltips();
    })
    .on("mouseout", function(e) {
      for (var edge of e.wire.net.edges) {
        var id = 'path#' + edge.id;
        d3.select(id).classed("hover",false);
      }
      hovered_edge.tooltip.transition()
        .duration(200)
        .style("opacity", 0)
        .remove();
      hovered_edge = null;
    })
    .on("click", function(e) {
      var tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0)
        .style("left", (d3.event.pageX + 10) + "px")
        .style("top", (d3.event.pageY + 5) + "px")
      tooltip.transition()
        .duration(200)
        .style("opacity", .9);
      stamped_edges.push({
        edge: e,
        tooltip: tooltip
      });
      tooltip.on("click", function() {
        if (window.getSelection().type != "Range") {
          var elem = d3.select(this).node();
          for (var i=0; i<stamped_edges.length; i++) {
            if (elem == stamped_edges[i].tooltip.node()) {
              d3.select(this).remove();
              stamped_edges.splice(i,1);
              break;
            }
          }
        }
      });
      tooltip.call(tooltip_drag);
      update_tooltips();
    });
}

//////////////////////////////////
function input_blurred() {
  var val = parseInt(this.value,16);
  if (isNaN(val)) {
    // restore original value from the corresponding net
    this.value = signal_value_hex(this.net.signal,this.net.width);
  }
  else {
    this.component.update({[this.name]:val});
    this.svg.update_all();
    this.value = signal_value_hex(this.net.signal,this.net.width);
  }
}

//////////////////////////////////
function input_keypressed() {
  if (event.key == "Enter") {
    this.blur();
  }
}

//////////////////////////////////
function attach_inputs(svg,component) {
  // attach input box for each bus input connector
  svg.selectAll(".connector.in.bus")
    .each(function(lbl) {
      var g = d3.select(this.parentNode);
      g.select("text").remove();
      var net = lbl.wire.net;
      var d3_input = g.append("foreignObject")
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
            .attr("value",signal_value_hex(net.signal,net.width));
      var input = d3_input.node();
      input.onkeypress = input_keypressed;
      input.onblur = input_blurred;
      input.net = lbl.wire.net;
      input.component = component;
      input.svg = svg;
    });
}

//////////////////////////////////
var Widget = function(widget_config) {
  for (var k in widget_config) {
    this[k] = widget_config[k];
  }
};

//////////////////////////////////
function get_wire_wrapper(component,wire) {
  function get_wire_value() {
    return component.get_net_signal(wire.net,wire.slice);
  }
  return get_wire_value;
}

//////////////////////////////////
function set_wire_wrapper(component,wire) {
  function set_wire_value(value) {
    return component.set_net_signal(wire.net,wire.slice,value);
  }
  return set_wire_value;
}

//////////////////////////////////
function resolve_references(component,node,partmap) {
  // resolve references to net and widget instances
  if (node.type == "connector" || node.type == "constant")
    node.wire.net = component.nets[node.wire.net];
  if (node.widget) {
    if (!widget_configs[node.widget]) {
      var err = "Widget " + node.widget + " not registered.";
      msgdiv.innerHTML = err;
      throw err;
    }
    node.widget = new Widget(widget_configs[node.widget]);
    node.width = node.widget.width;
    node.height = node.widget.height;
    var get_pin_value_funcs = {};   // mapping pin -> signal getter function
    var set_pin_value_funcs = {};   // mapping pin -> signal setter function
    for (var p of node.ports) {
      get_pin_value_funcs[p.name] = get_wire_wrapper(component,p.wire);
      set_pin_value_funcs[p.name] = set_wire_wrapper(component,p.wire);
    }
    node.widget.get_pin_value = get_pin_value_funcs;
    node.widget.set_pin_value = set_pin_value_funcs;
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
      var net = edge.wire.net;
      if (!net.hasOwnProperty('edges'))
        net.edges = []
      net.edges.push(edge);
    }
  }
  if (node.children) {
    for (var child of node.children) {
      resolve_references(component,child,partmap);
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
  resolve_references(component,config.graph,partmap);
  elk.layout(config.graph).then(function(layout) {
    var svg = d3.select(selector).append("svg")
                                   .attr("width", layout.width)
                                   .attr("height", layout.height);
    drawNode(svg,layout,component);
    for (var w of widgets) {
      w.setup(svg);
      w.root_svg = svg;
      w.component = component;
    }
    attach_events(svg,component);
    attach_inputs(svg,component);
    component.update();
    svg.update_all = update_all_wrapper(svg,component);
    svg.update_all();
  });
}

//////////////////////////////////
function register_widget(name,widget_config) {
  widget_configs[name] = widget_config;
}

//////////////////////////////////
exports.create = create;
exports.register_widget = register_widget;

}));

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
      if (n.svg) { // use provided svg when available
        d3.select(this).html(n.svg);
      }
      else if (n.type == "connector") { // I/O connector
        n.wire.net = component.nets[n.wire.net];
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
        n.wire.net = component.nets[n.wire.net];
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
        .each(function(p) { // resolve reference to net object
          if (p.wire)
            p.wire.net = component.nets[p.wire.net];
        })
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
    .each(function(e) { // resolve reference to net object
      e.wire.net = component.nets[e.wire.net];
    })
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
function update(svg,component) {
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
}

//////////////////////////////////
function attach_events(svg,component) {

  // prepare a tooltip box
  var tooltip = d3.select("body").append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

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
      var out = component.update({[c.wire.name]:signal});
      update(svg,component);
    });
  svg.selectAll("path.edge")
    .on("mouseover", function(e) {
      d3.select(this).classed("hover",true);
      tooltip.transition()
        .duration(200)
        .style("opacity", .9);
      var sigval = component.get_net_signal(e.wire.net, e.wire.slice);
      tooltip.html("<span class='signal'>" +
        e.name + " = 0x" + sigval.toString(16).toUpperCase() +
        "</span>"
        )
        .style("left", (d3.event.pageX + 10) + "px")
        .style("top", (d3.event.pageY + 5) + "px");
    })
    .on("mouseout", function(e) {
      d3.select(this).classed("hover",false);
      tooltip.transition()
        .duration(200)
        .style("opacity", 0);
    })
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
    update(this.svg,this.component);
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
function create(selector,config) {
  var elk = new ELK();
  elk.layout(graph).then(function(layout) {
    var svg = d3.select(selector).append("svg")
                                   .attr("width", layout.width)
                                   .attr("height", layout.height);
    drawNode(svg,layout,component);
    attach_events(svg,config.component);
    attach_inputs(svg,config.component);
    update(svg,config.component);
  });
}

//////////////////////////////////
exports.create = create;

}));

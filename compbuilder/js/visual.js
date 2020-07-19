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
const DRAW_CONN_IN = "M 0,0 h 14 l 6,6 l -6,6 h -14 z";
const DRAW_CONN_OUT = "M 20,0 h -14 l -6,6 l 6,6 h 14 z";

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
function drawChildren(svg,node) {
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
      else if (n.type == "connector") {
        d3.select(this)
          .append("path")
          .attr("class","connector " + n.direction)
          .attr("d", n.direction == "in" ? DRAW_CONN_IN : DRAW_CONN_OUT);
        n.node_id = "root"; // connectors are only attached to root node
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
        labelGroup.selectAll("text.label")
          .data(n.labels, function(lbl) { return lbl.id; })
        .enter()
          .append("text")
          .attr("class", "label " + nodeType)
          .attr("x", function(lbl) { return lbl.x; })
          .attr("y", function(lbl) { return lbl.y + lbl.height; })
          .text(function(lbl) { return lbl.text; });
        labelGroup.attr("transform", translate(n.x,n.y));
      }
    });

  // recursively draw node of each child, if available
  node.children.forEach(function(child) {
    if (child.children) {
      drawNode(svg,child);
    }
  });
}

//////////////////////////////////
function drawEdges(svg,node) {
  svg.selectAll("path.edge")
    .data(node.edges, function(e) { return e.id; })
  .enter()
    .append("path")
    .attr("id",function(e) { return e.id; })
    .attr("class",function(e) { return "edge " + e.sources[0]})
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
function drawNode(svg,node) {
  var group = svg.append("g");
  drawChildren(group,node);
  drawEdges(group,node);
  group.attr("transform", translate(node.x,node.y));
}

//////////////////////////////////
function update(svg,component) {
  svg.selectAll("path.edge")
    .classed("T", function(e) {
      return component.nets[e.wire.net].signal;
    });
  svg.selectAll("rect.port")
    .classed("T", function(p) {
      if (!(p.wire))
        return false; // XXX constant wire should have 'wire' attached as well
      else
        return component.nets[p.wire.net].signal;
    });
  svg.selectAll("path.connector")
    .classed("T", function(c) {
      return component.nets[c.wire.net].signal;
    });
}

//////////////////////////////////
function attach_inputs(svg,component) {
  svg.selectAll(".connector.in")
    .on("mouseover", function(c) {
      d3.select(this).classed("hover",true);
    })
    .on("mouseout", function(c) {
      d3.select(this).classed("hover",false);
    })
    .on("click", function(c) {
      var signal = component.nets[c.wire.net].signal;
      signal = signal ? 0 : 1;
      var out = component.update({[c.wire.name]:signal});
      update(svg,component);
    });
}

//////////////////////////////////
function create(selector,config) {
  var elk = new ELK();
  elk.layout(graph).then(function(layout) {
    var svg = d3.select(selector).append("svg")
                                   .attr("width", layout.width)
                                   .attr("height", layout.height);
    drawNode(svg,layout);
    attach_inputs(svg,config.component);
    update(svg,config.component);
  });
}

//////////////////////////////////
exports.create = create;

}));

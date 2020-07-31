/////////////////////////////////////////////////
compbuilder.register_widget('seven-segment',
{
  width: 80,
  height: 120,
  setup: function(root_svg) {
    this.svg.append("rect")
      .attr("height",this.height)
      .attr("width",this.width)
      .attr("stroke","grey")
      .attr("stroke-width","3px")
      .attr("fill","black");
    this.segments = {
      a: this.svg.append("path")
        .attr("d", "M 17,20 l4,-4 h40 l4,4 l-4,4 h-40 z")
        .attr("stroke-width",0),
      b: this.svg.append("path")
        .attr("d", "M 66,21 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      c: this.svg.append("path")
        .attr("d", "M 66,61 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      d: this.svg.append("path")
        .attr("d", "M 17,100 l4,-4 h40 l4,4 l-4,4 h-40 z")
        .attr("stroke-width",0),
      e: this.svg.append("path")
        .attr("d", "M 16,61 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      f: this.svg.append("path")
        .attr("d", "M 16,21 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      g: this.svg.append("path")
        .attr("d", "M 17,60 l4,-4 h40 l4,4 l-4,4 h-40 z")
        .attr("stroke-width",0)
    }
  },
  update: function() {
    for (var s in this.segments) {
      var val = this.get_pin_value[s]();
      if (val)
        this.segments[s].attr("fill","red");
      else
        this.segments[s].attr("fill","black");
    }
  }
});

/////////////////////////////////////////////////
compbuilder.register_widget('keypad',
{
  width: 105,
  height: 55,
  setup: function() {
    var self = this;
    this.svg.append("rect")
      .attr("height",this.height)
      .attr("width",this.width)
      .attr("stroke","grey")
      .attr("stroke-width","1px")
      .attr("fill","pink");

    for (var key_id = 0; key_id < 8; key_id++) {
      var x = key_id % 4;
      var y = Math.floor(key_id / 4);
      var pad = this.svg.append("circle")
        .attr("class","keypad")
        .attr("cx",x*25+15)
        .attr("cy",y*25+15)
        .attr("r",10)
        .attr("fill","black")
        .datum(key_id);
      pad.on("click", function(c) {
        var current = self.get_pin_value['keys']();
        var pad = d3.select(this);
        var key_id = pad.datum();
        current ^= (1 << key_id);
        self.set_pin_value['keys'](current);
        if (current & (1 << key_id))
          pad.attr("fill","yellow");
        else
          pad.attr("fill","black");
        self.root_svg.update_all();
      });
    }
  },
});

/////////////////////////////////////////////////
compbuilder.register_widget('clock',
{
  width: 46,
  height: 55,

  setup: function() {
    var self = this;
    self.svg.append("rect")
      .attr("height",self.height)
      .attr("width",self.width)
      .attr("rx",5)
      .attr("ry",5)
      .style("fill","yellow");

    // clock logo
    self.svg.append("path")
      .style("fill","none")
      .style("stroke","grey")
      .style("stroke-width","3px")
      .attr("d", "M 4,15 h11 v-10 h15 v10 h11");

    // stop button
    self.svg.append("rect")
      .attr("class","control")
      .attr("transform","translate(4,20)")
      .attr("height",16)
      .attr("width",18)
      .attr("rx",3)
      .attr("ry",3)
      .on("click",function() {
        self.set_clock_speed(self,0);
      });
    self.svg.append("path")
      .attr("class","control")
      .attr("transform","translate(4,20)")
      .style("stroke-width","0")
      .style("fill","blue")
      .attr("d","M 5,4 h8 v8 h-8 v-8 z");

    // step button
    self.svg.append("rect")
      .attr("class","control")
      .attr("transform","translate(23,20)")
      .attr("height",16)
      .attr("width",18)
      .attr("rx",3)
      .attr("ry",3)
      .on("click",function() {
        self.one_shot(self,50);
      });
    self.svg.append("path")
      .attr("class","control")
      .attr("transform","translate(23,20)")
      .style("stroke-width","0")
      .style("fill","blue")
      .attr("d","M 5,4 l5,4 l-5,4 v-8 m 5,0 h2 v8 h-2 v-8");

    // play button
    self.svg.append("rect")
      .attr("class","control")
      .attr("transform","translate(4,37)")
      .attr("height",16)
      .attr("width",18)
      .attr("rx",3)
      .attr("ry",3)
      .on("click",function() {
        self.set_clock_speed(self,1);
      });
    self.svg.append("path")
      .attr("class","control")
      .attr("transform","translate(4,37)")
      .style("stroke-width","0")
      .style("fill","blue")
      .attr("d","M 5,4 l8,4 l-8,4 v-8");

    // fast-forward button
    self.svg.append("rect")
      .attr("class","control")
      .attr("transform","translate(23,37)")
      .attr("height",16)
      .attr("width",18)
      .attr("rx",3)
      .attr("ry",3)
      .on("click",function() {
        self.set_clock_speed(self,50);
      });
    self.svg.append("path")
      .attr("class","control")
      .attr("transform","translate(23,37)")
      .attr("d","M 5,4 l5,4 l-5,4 v-8 m 5,0 l5,4 l-5,4 v-8");

    self.svg.selectAll("rect.control")
      .style("fill","white")
      .style("stroke","black")
      .style("stroke-width","0")
      .on("mouseover",function() {
        d3.select(this).style("stroke-width","2");
      })
      .on("mouseout",function() {
        d3.select(this).style("stroke-width","0");
      });
    self.svg.selectAll("path.control")
      .style("stroke-width","0")
      .style("fill","black")
      .style("pointer-events","none");
  },

  update: function() {
  },

  set_clock_speed: function(self,hz) {
    if (self._timer) clearTimeout(self._timer);
    if (hz) {
      self._timeout_ms = 1000/hz/2;
      self._trigger(self,1);
    }
    else {
      self.component.update({'clk':0});
      self.root_svg.update_all();
    }
  },

  one_shot: function(self,duration_ms) {
    if (self._timer) clearTimeout(self._timer);
    self.component.update({'clk':1});
    self.root_svg.update_all();
    self._timer = setTimeout(function() {
        self.component.update({'clk':0});
        self.root_svg.update_all();
    }, duration_ms);
  },

  _trigger: function(self,v) {
    self.component.update({'clk':v});
    self.root_svg.update_all();
    self._timer = setTimeout(function() {
      self._trigger(self,v^1);
    }, self._timeout_ms);
  },
});

/////////////////////////////////////////////////
compbuilder.register_widget('seven-segment',
{
  width: 80,
  height: 120,
  setup: function() {
    var self = this;
    self.svg.append("rect")
      .attr("height",self.height)
      .attr("width",self.width)
      .attr("stroke","grey")
      .attr("stroke-width","3px")
      .attr("fill","black");
    self.segments = {
      a: self.svg.append("path")
        .attr("d", "M 17,20 l4,-4 h40 l4,4 l-4,4 h-40 z")
        .attr("stroke-width",0),
      b: self.svg.append("path")
        .attr("d", "M 66,21 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      c: self.svg.append("path")
        .attr("d", "M 66,61 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      d: self.svg.append("path")
        .attr("d", "M 17,100 l4,-4 h40 l4,4 l-4,4 h-40 z")
        .attr("stroke-width",0),
      e: self.svg.append("path")
        .attr("d", "M 16,61 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      f: self.svg.append("path")
        .attr("d", "M 16,21 l4,4 v30 l-4,4 l-4,-4 v-30 z")
        .attr("stroke-width",0),
      g: self.svg.append("path")
        .attr("d", "M 17,60 l4,-4 h40 l4,4 l-4,4 h-40 z")
        .attr("stroke-width",0)
    }
  },
  update: function() {
    var self = this;
    for (var s in self.segments) {
      var val = self.get_pin_value[s]();
      if (val)
        self.segments[s].attr("fill","red");
      else
        self.segments[s].attr("fill","black");
    }
  }
});

/////////////////////////////////////////////////
compbuilder.register_widget('keyboard',
{
  width: 105,
  height: 55,
  setup: function() {
    var self = this;
    self.svg.append("rect")
      .attr("height",self.height)
      .attr("width",self.width)
      .attr("stroke","grey")
      .attr("stroke-width","1px")
      .attr("fill","pink");

    for (var key_id = 0; key_id < 8; key_id++) {
      var x = key_id % 4;
      var y = Math.floor(key_id / 4);
      var pad = self.svg.append("circle")
        .attr("class","keypad")
        .attr("cx",x*25+15)
        .attr("cy",y*25+15)
        .attr("r",10)
        .attr("fill","black")
        .datum(key_id);
      pad.on("click", function(c) {
        var current = self.get_pin_value['out']();
        var pad = d3.select(this);
        var key_id = pad.datum();
        current ^= (1 << key_id);
        self.set_pin_value['out'](current);
        if (current & (1 << key_id))
          pad.attr("fill","yellow");
        else
          pad.attr("fill","black");
        self.component.update();
        self.root_svg.update_all();
      });
    }
  },
});

/////////////////////////////////////////////////
compbuilder.register_widget('screen',
{
  width: 514,
  height: 258,
  color_on: [0,0,0],
  color_off: [224,255,224],
  setup: function() {
    var self = this;
    var canvas = self.svg.append("foreignObject")
      .attr("height",self.height)
      .attr("width",self.width)
      .style("border","1px solid lightgrey")
      .append("xhtml:div")
        .append("canvas")
          .attr("id","canvas")
          .attr("height",self.height)
          .attr("width",self.width)
          .style("position","fixed");

    self.ctx = canvas.node().getContext("2d");
    self.bitmap = self.ctx.createImageData(512,256);
    for (var i=0; i<self.bitmap.data.length; i += 4) {
      self.bitmap.data[i+0] = self.color_off[0];
      self.bitmap.data[i+1] = self.color_off[1];
      self.bitmap.data[i+2] = self.color_off[2];
      self.bitmap.data[i+3] = 255;
    }
    self.ctx.putImageData(self.bitmap,0,0);
    self._clk = 0;
  },
  trigger: function(w,s) {
    var self = this;
    if (w.clk && w.load && !self._clk) {
      self._clk = 1;
      var addr = w.address;
      var data = w.In;
      var img_idx = addr*16*4;
      for (var i=0; i<16; i++) {
        if (data & (1 << i)) {
          self.bitmap.data[img_idx+i*4+0] = self.color_on[0];
          self.bitmap.data[img_idx+i*4+1] = self.color_on[1];
          self.bitmap.data[img_idx+i*4+2] = self.color_on[2];
        }
        else {
          self.bitmap.data[img_idx+i*4+0] = self.color_off[0];
          self.bitmap.data[img_idx+i*4+1] = self.color_off[1];
          self.bitmap.data[img_idx+i*4+2] = self.color_off[2];
        }
      }
      self.ctx.putImageData(self.bitmap,0,0);
    }
    else if (!w.clk && self._clk) {
      self._clk = 0;
    }
  },
});

/////////////////////////////////////////////////
compbuilder.register_widget('rom',
{
  width: 160,
  height: 80,
  setup: function() {
    var self = this;
    var progbox = self.svg.append("foreignObject")
      .attr("width",160)
      .attr("height",80)
      .style("border","1px solid lightgrey")
      .append("xhtml:div")
        .append("textarea")
          .attr("id","progbox")
          .style("width","100%")
          .style("height","78px")
          .style("resize","none")
          .style("box-sizing","border-box")
          .style("position","fixed");
    self.data_to_textarea(self.part.states.data,progbox);
    progbox.on("blur",function() {
      self.textarea_to_data(progbox,self.part.states.data);
    });
  },

  data_to_textarea: function(data,textarea) {
    var contents = [];
    for (var word of data) {
      var s = "000000000" + word.toString(16).toUpperCase();
      contents.push(s.substr(s.length-4));
    }
    textarea.property("value",contents.join("\n"));
  },

  textarea_to_data: function(textarea,data) {
    var self = this;
    data.length = 0;
    for (var line of textarea.property("value").split("\n")) {
      var word = parseInt(line,16);
      if (!isNaN(word)) {
        data.push(word);
      }
    }
    self.data_to_textarea(data,textarea);
    self.component.update();
    self.root_svg.update_all();
  }
});

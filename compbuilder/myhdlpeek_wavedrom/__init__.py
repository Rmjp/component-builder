# MIT license
#
# Copyright (C) 2017 by XESS Corp.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

# ----------------------------------------------------------------------------
# This function is taken from myhdlpeek https://github.com/xesscorp/myhdlpeek
# (MIT License)
# ----------------------------------------------------------------------------

import json

import IPython.display as DISP

def is_in_colab():
    try:
        import google.colab
        return True
    except:
        return False

def wavejson_to_wavedrom(wavejson, width=None, skin='default'):
    '''
    Create WaveDrom display from WaveJSON data.
    This code is from https://github.com/witchard/ipython-wavedrom.
    Inputs:
      width: Width of the display window in pixels. If left as None, the entire
             waveform will be squashed into the width of the page. To prevent
             this, set width to a large value. The display will then become scrollable.
      skin:  Selects the set of graphic elements used to draw the waveforms.
             Allowable values are 'default' and 'narrow'.
    '''

    # Set the width of the waveform display.
    style = ''
    if width != None:
        style = ' style="width: {w}px"'.format(w=str(int(width)))

    # Generate the HTML from the JSON.
    htmldata = '<div{style}><script type="WaveDrom">{json}</script></div>'.format(
        style=style, json=json.dumps(wavejson))

    if is_in_colab():
        setup = ('''
<script src="https://wavedrom.com/skins/{skin}.js" type="text/javascript"></script>'''.format(skin=skin) + '''
<script src="https://wavedrom.com/wavedrom.min.js" type="text/javascript"></script>
<script>
  if (WaveDrom == undefined) {
    setTimeout(function(){WaveDrom.ProcessAll();}, 1000);
  } else {
    WaveDrom.ProcessAll();
  }
</script>''' + htmldata)
        DISP.display_html(DISP.HTML(setup))
    else:
        DISP.display_html(DISP.HTML(htmldata))

        # Trigger the WaveDrom Javascript that creates the graphical display.
        DISP.display_javascript(
            DISP.Javascript(
                data='WaveDrom.ProcessAll();',
                lib=[
                    'http://wavedrom.com/wavedrom.min.js',
                    'http://wavedrom.com/skins/{skin}.js'.format(skin=skin)
                ]))
 


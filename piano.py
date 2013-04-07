import gtk
import cairo
import fluidsynth

class Piano(gtk.DrawingArea):
    def __init__(self, synth):
        super(Piano, self).__init__()
        # two sets that contain information for redrawing the keyboard
        self.pressed_white_keys = set()
        self.pressed_black_keys = set()
        self.playing=set()
        self.octave = 5
        self.synth = synth 
        # a few constants that make the keyboard look nice
        self.invnKeys = 1/42.0 #1 divided by number of white keys
        self.blackOffset = self.invnKeys*(2./3) #magic ratio used in the drawing method.
        self.keyboardShift = 2 # a shifting constant that determines where c5 appears on board
        keyWidth = 27 # width of a white key in pixels

        #gtk.DrawingArea doesn't natively accept these two events, so add them in
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK
            |gtk.gdk.BUTTON_RELEASE_MASK)
        self.set_flags(gtk.CAN_FOCUS)

        self.set_size_request(int(keyWidth/self.invnKeys), 120)

        self.connect("expose_event", self.expose)
        self.connect("button-press-event", self.btn_press)
        self.connect("button-release-event", self.btn_release)
        self.connect("key-press-event", self.key_press)
        self.connect("key-release-event", self.key_release)
    
    def clear_pressed_keys(self): # used when we want to interrupt the normal flow of things
        self.pressed_white_keys.clear()
        self.pressed_black_keys.clear()

    # presses a list of notes passed in from other code rather than an X event. Used in the XPlay thread
    def ext_note_press(self, noteVals):
        for noteVal in noteVals:
            if noteVal%12 in [1,3,6,8,10]:
                self.pressed_black_keys.add(gtrans[noteVal%12] + (noteVal/12)*7)
            else:
                self.pressed_white_keys.add(gtrans[noteVal%12] + (noteVal/12)*7)
            self.synth.noteon(0, noteVal, 100)
        self.redraw_board()

    def ext_note_release(self, noteVals):
        for noteVal in noteVals:
            if noteVal%12 in [1,3,6,8,10]:
                self.pressed_black_keys.discard(gtrans[noteVal%12] + (noteVal/12)*7)
            else:
                self.pressed_white_keys.discard(gtrans[noteVal%12] + (noteVal/12)*7)
            self.synth.noteoff(0, noteVal)

        self.redraw_board()

    # hits the key that corresponds to the keyboard action. 
    def key_press(self, widget, key):
        if(key.keyval < 58 and key.keyval > 47): #set the octave when num key is pressed
            self.octave = key.keyval - 48
            return True
        if(not (key.keyval in keymap)):
            return True

        note = keymap[key.keyval] + self.octave*12
        
        # the gtrans map maps the note (in mod 12) to the appropriate displayed key
        # which is in mod 7
        if(keymap[key.keyval] in [1,3,6,8,10,13,15,18]):
            self.pressed_black_keys.add(gtrans[keymap[key.keyval]] + self.octave * 7)
        else:
            self.pressed_white_keys.add(gtrans[keymap[key.keyval]] + self.octave * 7)

        self.redraw_board()

        # this prevents the spam of key_pressed events from messing up sustain
        if(not (note in self.playing)):
            self.synth.noteon(0, note, 100)
            self.playing.add(note)

        return True

    def key_release(self, widget, key):
        if(key.keyval < 58 and key.keyval > 47): #ignore these released keys
            return True

        if not(key.keyval in keymap):
            return True

        if(keymap[key.keyval] in [1,3,6,8,10,13,15,18]):
            self.pressed_black_keys.discard(gtrans[keymap[key.keyval]] + self.octave * 7)
        else:
            self.pressed_white_keys.discard(gtrans[keymap[key.keyval]] + self.octave * 7)

        self.redraw_board()

        note = keymap[key.keyval] + self.octave*12
        self.synth.noteoff(0, note)
        self.playing.discard(note)
        return True


        # presses the keys that originate from mouse-click action
    def btn_press(self, widget, event):
        self.grab_focus()
        key = self.calculate_key(event.x, event.y)

        # the rev_gtrans maps go in the opposite direction: from the mod 7
        # graphics to the mod 12 notes
        if(key[0] == "white"):
            self.pressed_white_keys.add(key[1])
            note = white_rev_gtrans[key[1] % 7] + (key[1] / 7)*12

        if(key[0] == "black"):
            self.pressed_black_keys.add(key[1])
            note = black_rev_gtrans[key[1] % 7] + (key[1] / 7)*12

        self.redraw_board()

        if(not (note in self.playing)):
            self.synth.noteon(0, note, 100)
            self.playing.add(note)
        
    def btn_release(self, widget, event):
        key = self.calculate_key(event.x, event.y)
        if(key[0] == "white"):
            self.pressed_white_keys.discard(key[1])
            note = white_rev_gtrans[key[1] % 7] + (key[1] / 7)*12

        if(key[0] == "black"):
            self.pressed_black_keys.discard(key[1])
            note = black_rev_gtrans[key[1] % 7] + (key[1] / 7)*12

        self.redraw_board()
        
        self.synth.noteoff(0, note)
        self.playing.discard(note)

    # this method determines which key was pressed depending on the x,y coords
    # of the mouse click
    def calculate_key(self,x, y):
        width = self.allocation.width
        height = self.allocation.height
        
        #reminder : invnKeys is 1/# of whites
        key_pos = int(x/(self.invnKeys*width)) # nominal pos. of the clicked key

        # nothing below the 0.6 line could possibly be a black key
        if(y > 0.6*height):
            return tuple(["white", key_pos + self.keyboardShift*7]) 

        black_pos = int((x - width*self.blackOffset)/(self.invnKeys*width)) # shift back blackOffset units and get the equivalent position
        
        # the second part of this if statement constrains the x coord to lie within 
        # the black part. The width of the black key is 2/3 that of the white key, so
        # we want the fractional part of the click's shifted position to be less than that
        if(black_pos % 7 in [0,1,3,4,5] and (x - width*self.blackOffset)/(self.invnKeys*width) - black_pos < 0.66):
            return tuple(["black", black_pos + self.keyboardShift*7])

        return tuple(["white", key_pos + self.keyboardShift*7])

    # this code was found in an online tutorial about how to draw a clock in GTK+
    # http://www.oluyede.org/blog/writing-a-widget-using-cairo-and-pygtk-28-part-2/
    def redraw_board(self):
        if self.window:
            alloc = self.get_allocation()
            rect = gtk.gdk.Rectangle(0, 0, alloc.width, alloc.height)
            self.window.invalidate_rect(rect, True)
            self.window.process_updates(True)
    
    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        cr.set_line_width(1)
        self.redraw(cr)

    # This method does the heavy lifting of drawing the keyboard using the cairo library 
    def redraw(self, cr):
        width = self.allocation.width
        height = self.allocation.height

        for i in range(int(1/self.invnKeys)):
            cr.set_source_rgb(0,0,0)
            cr.move_to(width*i*self.invnKeys, 0)
            cr.line_to(width*i*self.invnKeys, height)
            cr.stroke()
            # These rectangles represent the keys that are depressed. Shade them in a different color
            if(i + self.keyboardShift*7 in self.pressed_white_keys):
                cr.save()
                cr.rectangle(width*i*self.invnKeys, 0, width*self.invnKeys, height)
                cr.clip()
                cr.set_source_rgb(0,0,1.0)
                cr.paint()
                cr.restore()
        for i in range(int(1/self.invnKeys)):
            if i%7 in [0,1,3,4,5]:
                cr.set_source_rgb(0,0,0)
                cr.rectangle(width*i*self.invnKeys + width*self.blackOffset, 0, width*self.blackOffset, height*0.6)
                cr.fill()
                if(i + self.keyboardShift*7 in self.pressed_black_keys):
                    cr.save()
                    cr.set_operator(cairo.OPERATOR_SOURCE)
                    cr.set_source_rgb(0,0,1.0)
                    cr.rectangle(width*i*self.invnKeys + width*self.blackOffset, 0, width*self.blackOffset, height*0.6)
                    cr.fill()
                    cr.restore()
        
        return False

# maps the keyboard keys to note values
keymap = {97:0, 119:1, 115:2, 101:3, 100:4, 102:5, 116:6, 103:7,
    121:8, 104:9, 117:10, 106:11, 107:12, 111:13, 108:14, 112:15, 59:16, 
    39:17, 93:18}

# maps note values to keyboard positions
gtrans = {0:0, 1:0, 2:1, 3:1, 4:2, 5:3, 6:3, 7:4, 8:4, 9:5, 10:5, 11:6,
    12:7, 13:7, 14:8, 15:8, 16:9, 17:10, 18:10}

# maps keyboard positions back to note values
white_rev_gtrans = {0:0, 1:2, 2:4, 3:5, 4:7, 5:9, 6:11}
black_rev_gtrans = {0:1, 1:3, 3:6, 4:8, 5:10}

#!/usr/bin/python
#playxml.py - plays a xml file describing some music
import fluidsynth
import piano
import gtk
from xplay import XPlay
from sys import argv

class PlayPiano():
    def __init__(self, synth):
        window = gtk.Window()
        window.connect("key-press-event",(lambda x,y:False))
        window.connect("key-release-event",(lambda x,y:False))
        topVBox = gtk.VBox()
        toolbar_and_measure = gtk.HBox()
        self.XMLplayer = None
    
        keyboard = piano.Piano(synth)
        menu = self.makeMenu(keyboard)
        self.controlBar = self.makeToolBar()
    
        m_label = gtk.Label()
        m_label.set_text("Measure:")
    
        self.m_number = gtk.Entry()
        self.m_number.set_text("0")
        self.m_number.set_max_length(4)
        self.m_number.set_width_chars(4)
    
        toolbar_and_measure.pack_start(self.controlBar)
        toolbar_and_measure.pack_end(self.m_number,expand=False, fill=False)
        toolbar_and_measure.pack_end(m_label, expand=False, fill=False)
        topVBox.pack_start(menu)
        topVBox.pack_start(toolbar_and_measure)
        topVBox.pack_start(keyboard)
        window.add(topVBox)
        window.show_all()
    
        window.connect("destroy",self.main_quit)
        gtk.main()

    def main_quit(self,obj):
        if(self.XMLplayer != None):
            self.XMLplayer.stop()
        gtk.main_quit()
    
    def makeMenu(self,keyboard):
        menubar = gtk.MenuBar()
        fileMenu = gtk.Menu()
        fileMenuItem = gtk.MenuItem("File")
        fileMenuItem.set_submenu(fileMenu)
    
        exitItem = gtk.MenuItem("Exit")
        exitItem.connect("activate", self.main_quit)
        fileMenu.append(exitItem)
    
        openItem = gtk.MenuItem("Open file")
        openItem.connect("activate", self.runDialog, keyboard)
        fileMenu.append(openItem)
    
        menubar.append(fileMenuItem)
        return menubar
    
    def runDialog(self, obj, keyboard):
        fileDialog = self.makeFileDialog()
        response = fileDialog.run()
        if response == gtk.RESPONSE_OK:
            self.XMLplayer = XPlay(fileDialog.get_filename(), keyboard, self.m_number)
            self.activate_toolbar_buttons()
            self.XMLplayer.start()
        fileDialog.destroy()
    
    def activate_toolbar_buttons(self):
        buttons = self.controlBar.get_children()
        buttondict = {0:self.XMLplayer.play, 1:self.XMLplayer.pause, 2:self.XMLplayer.seek, 3:self.XMLplayer.stop}
        for button in buttons:
            button.connect("clicked",buttondict[buttons.index(button)])
        self.m_number.connect("activate",self.XMLplayer.seek,False)
    
    def makeFileDialog(self):
        fileD = gtk.FileChooserDialog(title="Open..", action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                      buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        fileD.set_current_folder(".")
        return fileD
    
    def makeToolBar(self):
        bar = gtk.Toolbar()
        #initialize some icon images and buttons Requires a ./icons directory
        play_icon = gtk.Image()
        play_icon.set_from_file("./icons/play.png")
        play_button = gtk.ToolButton(play_icon)
        pause_icon = gtk.Image()
        pause_icon.set_from_file("./icons/pause.png")
        pause_button = gtk.ToolButton(pause_icon)
        rewind_icon = gtk.Image()
        rewind_icon.set_from_file("./icons/rewind.png")
        rewind_button = gtk.ToolButton(rewind_icon)
        stop_icon = gtk.Image()
        stop_icon.set_from_file("./icons/stop.png")
        stop_button = gtk.ToolButton(stop_icon)
        #display measure number
        #put stuff into the toolbar
        bar.insert(play_button,0)
        bar.insert(pause_button,1)
        bar.insert(rewind_button,2)
        bar.insert(stop_button,3)
    
        return bar
    

#synthesizer initialization
fs = fluidsynth.Synth()
fs.start()
soundfont = fs.sfload("sound.sf2")
fs.program_select(0,soundfont,0,1)

piano_window = PlayPiano(fs)

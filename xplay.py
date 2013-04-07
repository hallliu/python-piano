import time
import xml.etree.cElementTree as ET
import threading
import gtk
gtk.threads_init()

#two dictionaries for mapping strings to notes
noteDict = {"c":0,"d":2,"e":4,"f":5,"g":7,"a":9,"b":11}
sharpMap = {"#":1,"@":-1}

def noteToValue(note): #converts a note string to a integer note value
    result = noteDict[note[0]]+12*int(note[1])
    if len(note) == 3:
        result += sharpMap[note[2]]
    return result

def make_beat_list(nmeasures, beats): #make a list of beats on which notes fall
    start = 0
    result = map((lambda x: x + start), beats)
    for n in range(start + 1, nmeasures+1):
        result = result + map((lambda x: x + n), beats)
    return result

class XPlay(threading.Thread):
    stopthread = threading.Event()
    # the playing event affects the pause/start functionality
    playing = threading.Event()
    position = 0

    def play(self,widget):
        self.playing.set()

    def pause(self,widget):
        self.playing.clear()

    def stop(self, widget=None):
        self.playing.set()
        self.stopthread.set()
        self.pianoObj.clear_pressed_keys()
    
    # starts the music at whereever the measure indicator points to or zero, depending on value of rewind
    def seek(self,widget,rewind=True):
        if rewind:
            measure = 0
        else:
            # the -1 at the end reflects the fact that position 0 is the start of measure 1
            measure = int(self.m_number_control.get_text()) - 1
        beatlist = make_beat_list(self.duration, self.beats)
        
        # nominal position is measure number times beats per measure times number of subbeats.
        # add in the pickup beat correction afterwards
        self.position = measure*self.beats_per_measure*len(self.beats) + beatlist.index(self.pickup_beat)

        #get the updated tempo
        for n in self.tempoChanges.keys():
            if beatlist.index(n) <= self.position:
                self.tempo = self.tempoChanges[n]
        self.pianoObj.clear_pressed_keys()

    def __init__(self, XMLFileName, pianoObj, m_number_control):
        self.xmlFile = XMLFileName
        self.pianoObj = pianoObj
        self.m_number_control = m_number_control

        #XML parsing
        music = ET.parse(self.xmlFile)
        self.sheet = music.getroot()
        self.duration = int(self.sheet.get("duration"))
        self.beats_per_measure = int(self.sheet.get("timesig"))
        self.pickup_beat = float(self.sheet.get("offset"))

        #get a list of beats
        self.beats = map(float, self.sheet.get("beats").split(","))

        #get a list of tempo changes so we don't keep querying the XML file
        self.tempoChangeElems = self.sheet.findall(".//tempo")
        self.tempoChanges = dict()
        for n in self.tempoChangeElems:
            self.tempoChanges[int(n.get("start"))] = int(n.text)
        
        #set initial tempo
        self.tempo = self.tempoChanges[0]

        threading.Thread.__init__(self)

    def run(self): #function to play the xml file
        beatlist = make_beat_list(self.duration, self.beats)
        while self.position in range(len(beatlist)):
            self.playing.wait()
            if self.stopthread.isSet():
                break
            i = self.position
            self.m_number_control.set_text(str(int(
                (float(i)-beatlist[:20].index(self.pickup_beat))/(len(self.beats)*self.beats_per_measure)
                ) + 1)) #stupid type system...

            gtk.threads_enter()
            #find the notes that are to be turned on and off at this beat
            noteOnList = self.sheet.findall(".//playingfrom[@start='"+str(beatlist[i])+"']/..")
            noteOffList = self.sheet.findall(".//playingfrom[@end='"+str(beatlist[i])+"']/..")
            self.tempo = self.tempoChanges.get(beatlist[i], self.tempo)
        
            self.pianoObj.ext_note_release(map((lambda x: noteToValue(x.get("value"))),noteOffList))
            gtk.threads_leave()
            time.sleep(0.05) #time delay to make keys flash for repeat notes
            if self.stopthread.isSet():
                break
            gtk.threads_enter()
            self.pianoObj.ext_note_press(map((lambda x: noteToValue(x.get("value"))),noteOnList))
            
            gtk.threads_leave()
            self.position += 1
            if i < len(beatlist) - 1:
                time.sleep(60*(beatlist[i+1]-beatlist[i])/self.tempo-0.05)

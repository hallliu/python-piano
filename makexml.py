#!/usr/bin/python
import xml.etree.ElementTree as ET
from optparse import OptionParser
import sys
#parse command line opts
optparser = OptionParser()
optparser.add_option("-o","--output", dest="xmlout", default="out.xml")
optparser.add_option("-f","--offset", dest="offset", type="float", default=0)
(options, args) = optparser.parse_args()

mus_in = open(args[0],"r")
print "Creating new XML file"
xmlFile = ET.Element("sheet")
voice = ET.Element("voice")
xmlFile.append(voice)
noteList = []
offset = options.offset # ease of writing when we have a pickup

circle_of_fifths = ["f","c","g","d","a","e","b"]
key = 0
measure=0
end = 0
# make provisions for key signature. range is from -7(Cb) to 7(C#)
def key_transform (noteVal, key):
    if(len(noteVal) == 3 or key == 0):
        return noteVal #don't touch the accidentals or if we're in C
    if key < 0:
        if noteVal[0] in circle_of_fifths[7+key:]:
            return (noteVal + "@")
    if key > 0:
        if noteVal[0] in circle_of_fifths[:key]:
            return (noteVal + "#")
    return noteVal

for line in mus_in:
    # will try to clean up this ugly sequence later
    if line[0] == '#':
        continue
    components = line.split()
    if(components[0] == "tempo"):
        tempoElem = ET.Element("tempo",attrib={"start":str(int(round(end,2)))})
        tempoElem.text = components[1]
        xmlFile.append(tempoElem)
        continue
    if(components[0] == "beats"):
        xmlFile.set("beats",components[1])
        continue
    if(components[0] == "key"):
        key = int(components[1])
        continue
    if(components[0] == "timesig"):
        timesig = int(components[1])
        xmlFile.set("timesig",components[1])
        continue
    if(components[0] == "measure"):
        measure = int(components[1])
        continue

    noteVal = key_transform(components[0],key)
    start = float(components[1]) + offset + (measure - 1)*timesig
    end = start + float(components[2])
    #create the playingfrom element
    playElem = ET.Element("playingfrom",attrib={"start":str(round(start,2)), "end":str(round(end,2))})
    
    if noteVal in noteList:
        noteElem = xmlFile.find(".//note[@value='"+noteVal+"']")
        noteElem.append(playElem)
    else:
        noteList.append(noteVal)
        newNote = ET.Element("note",attrib={"value":noteVal})
        newNote.append(playElem)
        voice.append(newNote)

xmlFile.set("duration",str(int(end)))
xmlFile.set("offset",str(offset))
ET.ElementTree(xmlFile).write(options.xmlout)

#!/usr/bin/python
#playxml.py - plays a xml file describing some music
import fluidsynth
import time
from sys import argv
import xml.etree.ElementTree as ET

#two dictionaries that contain musical data
noteDict = {"c":0,"d":2,"e":4,"f":5,"g":7,"a":9,"b":11}
sharpMap = {"#":1,"@":-1}

def noteToValue(note): #converts a note string to a integer note value
    result = noteDict[note[0]]+12*int(note[1])
    if len(note) == 3:
        result += sharpMap[note[2]]
    return result

def make_beat_list(nmeasures, beats): #make a list of beats on which notes fall
    if len(argv) == 3: #set a starting beat
        start = int(argv[2]) - 1
    else:
        start = 0
    result = map((lambda x: x + start), beats)
    for n in range(start + 1, nmeasures+1):
        result = result + map((lambda x: x + n), beats)
    return result

#XML parsing
music = ET.parse(argv[1])
sheet = music.getroot()
duration = int(sheet.get("duration"))

#get a list of tempo changes so we don't keep querying the XML file
tempoChangeElems = sheet.findall(".//tempo")
tempoChanges = dict()
for n in tempoChangeElems:
    tempoChanges[int(n.get("start"))] = int(n.text)

#set initial tempo
tempo = tempoChanges[0]
#get a list of beats
beats = map(float, sheet.get("beats").split(","))

#synthesizer initialization
fs = fluidsynth.Synth()
fs.start()
soundfont = fs.sfload("sound.sf2")
fs.program_select(0,soundfont,0,1)

beatlist = make_beat_list(duration, beats)
for i in range(len(beatlist)):
    #find the notes that are to be turned on and off at this beat
    noteOnList = sheet.findall(".//playingfrom[@start='"+str(beatlist[i])+"']/..")
    noteOffList = sheet.findall(".//playingfrom[@end='"+str(beatlist[i])+"']/..")
    tempo = tempoChanges.get(beatlist[i], tempo)

    for n in noteOffList:
        noteVal = noteToValue(n.get("value"))
        fs.noteoff(0,noteVal)
    for n in noteOnList:
        noteVal = noteToValue(n.get("value"))
        fs.noteon(0,noteVal,100)
    if i < len(beatlist) - 1:
        time.sleep(60*(beatlist[i+1]-beatlist[i])/tempo)

# -*- coding: utf-8 -*-
"""
Handles the input, output, and representation of midi files
"""

from mido import MidiFile
from mido import MidiTrack
import numpy as np
import mido
import pdb

timestepsPerBeat = 4

def rescaleToTimesteps(ticks_per_beat, time):
    return round((time/ticks_per_beat)*timestepsPerBeat)

def rescaleToTicks(ticks_per_beat, time):
    return round((time/timestepsPerBeat)*ticks_per_beat)

class Note:

    """
    Takes the pitch (as in midi format), the start and the duration of the 
    note in timesteps
    """
    def __init__(self,pitch,start,duration):
        self.pitch = pitch
        self.start = start
        self.duration = duration        

class Track:
    
    def __init__(self, notes=None, barLen=np.inf):
        self.notes = []
        self.barLen = barLen
        self.length = 0
        if not notes is None:
            for n in notes:
                self.addNote(n)
       
    def addNote(self, note):
        self.notes.append(note)
        if note.start + note.duration > self.length:
            self.length = note.start + note.duration
   
    def isMonophonic(self):
        lastEnd = 0
        for note in self.notes:
            if note.start < lastEnd:
                return False
            lastEnd = note.start + note.duration
        return True
        
    def polyphonicPercentage(self):
        polyphonicCount = 0
        nextTime = 0
        currentTime = 0
        for note in self.notes:
            endTime = max(currentTime, note.start)
            if note.start < nextTime and note.start + note.duration > currentTime:
                startTime = max(currentTime, note.start)
                endTime = min(note.start + note.duration, nextTime)
                polyphonicCount += endTime - startTime
            nextTime = max(nextTime, note.start + note.duration)
            currentTime = endTime
        return polyphonicCount / self.length
    
    def uniqueNotes(self):
        pitches = [n.pitch for n in self.notes]
        return len(set(pitches))
            
        
def concatenateTracks(tracks):
    barLen = np.inf
    if len(tracks) > 0:
        barLen = tracks[0].barLen
        for t in tracks:
            if t.barLen != barLen:
                pdb.set_trace()
            assert t.barLen == barLen, "All concatenating tracks must have the same bar length"
    trackOut = Track(barLen=barLen)
    cumulativeTime = 0
    for track in tracks:
        for note in track.notes:
            newNote = Note(note.pitch, note.start+cumulativeTime, note.duration)
            trackOut.addNote(newNote)
        cumulativeTime = cumulativeTime + track.length
    return trackOut

# Splits the given track into two tracks, trackA [0,splitPoint) and trackB [splitPoint,END) 
# Preserves the original track, simply creates 2 new tracks   
def splitTrack(track, splitPoint):
    trackA = Track(barLen = track.barLen)
    trackB = Track(barLen = track.barLen)
    for n in track.notes:
        if n.start < splitPoint:
            if n.start + n.duration <= splitPoint:
                trackA.addNote(Note(n.pitch, n.start, n.duration))
            else:
                trackA.addNote(Note(n.pitch, n.start, splitPoint - n.start))
                trackB.addNote(Note(n.pitch, splitPoint, n.start + n.duration - splitPoint))
        else:
            trackB.addNote(Note(n.pitch, n.start - splitPoint, n.duration))
    return (trackA,trackB)
    
    
def makeTrackFromMidi(mid, trackNum):
    track = Track()
    currentTime = 0
    lastNoteStarted = [0]*128
    timeSignature = getMidiTimeSignature(mid)
    numerator = 4
    if not timeSignature is None:
        numerator = timeSignature[0][0]
    track.barLen = int(timestepsPerBeat * numerator)
    for message in mid.tracks[trackNum]:
        currentTime = currentTime + message.time
        if message.type == 'note_on' or message.type == 'note_off':
            pitch = message.note
            # Note goes on
            if message.velocity > 0 and message.type == 'note_on':
                lastNoteStarted[pitch] = currentTime
            # Note goes off
            else:
                difference = currentTime - lastNoteStarted[message.note]
                note = Note(pitch, rescaleToTimesteps(mid.ticks_per_beat,
                                                      lastNoteStarted[pitch]),
                            rescaleToTimesteps(mid.ticks_per_beat,difference))
                track.addNote(note)
    return track
    
def makeMidiFromTrack(track, ticksPerBeat, tempo=500000, timeSignature = (4,4,24,8)):
    midi = MidiFile(ticks_per_beat=ticksPerBeat)
    midi.add_track()
    if not isinstance(tempo, int):
        pdb.set_trace()
    midi.tracks[0].append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
    midi.tracks[0].append(mido.MetaMessage('time_signature', time=0,
                                           numerator = timeSignature[0],
                                           denominator = timeSignature[1],
                                           clocks_per_click = timeSignature[2],
                                           notated_32nd_notes_per_beat = timeSignature[3]))
                                
    midiEvents = len(track.notes)*2*[None]
    for i in range(len(track.notes)):
        midiEvents[i*2] = (True, track.notes[i].pitch,
                           rescaleToTicks(ticksPerBeat, track.notes[i].start))
        midiEvents[(i*2)+1] = (False, track.notes[i].pitch,
                               rescaleToTicks(ticksPerBeat, track.notes[i].start + track.notes[i].duration))
    midiEvents.sort(key = lambda tup: tup[2])
    eventTime = 0
    for event in midiEvents:
        lastEvent = eventTime
        eventTime = event[2]
        if event[0]:
            midi.tracks[0].append(mido.Message('note_on', note=event[1], velocity=64,
                                              time=eventTime-lastEvent))
        else:
            midi.tracks[0].append(mido.Message('note_off', note=event[1], velocity=127,
                                              time=eventTime-lastEvent))
        if eventTime-lastEvent < 0:
            pdb.set_trace()
            print("Whoops.")
    """
    for n in track.notes:
        lastEvent = eventTime
        eventTime = rescaleToTicks(ticksPerBeat, n.start)
        midi.tracks[0].append(mido.Message('note_on', note=n.pitch, velocity=64,
                                          time=eventTime-lastEvent))
        if eventTime-lastEvent < 0:
            pdb.set_trace()
            print("Whoops.")
        lastEvent = eventTime
        eventTime = rescaleToTicks(ticksPerBeat, n.start + n.duration)
        midi.tracks[0].append(mido.Message('note_off', note=n.pitch, velocity=127,
                                          time=eventTime-lastEvent))
        if eventTime-lastEvent < 0:
            pdb.set_trace()
            print("Whoopsy.")
    """
    return midi

# Returns the time signature of the midi, or None if the midi does not contain
# exactly one time signature message
def getMidiTimeSignature(mid):
    timeSignatures = []
    for track in mid.tracks:
        for message in track:
            if message.type == 'time_signature':
                timeSignature = (message.numerator,
                                 message.denominator,
                                 message.clocks_per_click,
                                 message.notated_32nd_notes_per_beat)
                timeSignatures.append(timeSignature)
    return timeSignatures

# Returns the first listed tempo of the midi, or None if the midi does not 
# contain a tempo message
def getMidiTempo(mid):
    tempos = []
    for track in mid.tracks:
        for message in track:
            if message.type == 'set_tempo':
                tempos.append(message.tempo)
    return tempos
                

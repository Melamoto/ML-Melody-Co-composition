# -*- coding: utf-8 -*-
"""
Handles the input, output, and representation of midi files
"""

from mido import MidiFile
from mido import MidiTrack
import mido

timestepsPerBeat = 16

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
    
    def __init__(self):
        self.notes = []
        self.length = 0
       
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
        
def makeTrackFromMidi(midi):
    assert len(midi.tracks) == 1, "Midi file must contain only 1 track"
    track = Track()
    currentTime = 0
    lastNoteStarted = [0]*128
    for message in midi.tracks[0]:
        currentTime = currentTime + message.time
        if message.type == 'note_on' or message.type == 'note_off':
            pitch = message.note
            # Note goes on
            if message.velocity > 0:
                lastNoteStarted[pitch] = currentTime
            # Note goes off
            else:
                difference = currentTime - lastNoteStarted[message.note]
                note = Note(pitch, rescaleToTimesteps(midi.ticks_per_beat,
                                                      lastNoteStarted[pitch]),
                            rescaleToTimesteps(midi.ticks_per_beat,difference))
                track.addNote(note)
    return track
    
def makeMidiFromTrack(track, ticksPerBeat, tempo=800000):
    midi = MidiFile(ticks_per_beat=ticksPerBeat)
    midi.add_track()
    midi.tracks[0].append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
    eventTime = 0
    for n in track.notes:
        lastEvent = eventTime
        eventTime = rescaleToTicks(ticksPerBeat, n.start)
        midi.tracks[0].append(mido.Message('note_on', note=n.pitch, velocity=64,
                                          time=eventTime-lastEvent))
        lastEvent = eventTime
        eventTime = rescaleToTicks(ticksPerBeat, n.start + n.duration)
        midi.tracks[0].append(mido.Message('note_off', note=n.pitch, velocity=127,
                                          time=eventTime-lastEvent))
    return midi

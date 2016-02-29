# -*- coding: utf-8 -*-
"""
Handles the input, output, and representation of midi files
"""

from mido import MidiFile

timestepsPerBeat = 16

def rescaleToTimesteps(midi, time):
    return int((time/midi.ticks_per_beat)*timestepsPerBeat)

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
                note = Note(pitch, rescaleToTimesteps(midi,lastNoteStarted[pitch]),\
                rescaleToTimesteps(midi,difference))
                track.addNote(note)
    return track
    


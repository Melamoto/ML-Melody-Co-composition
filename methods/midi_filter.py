# -*- coding: utf-8 -*-

from mido import MidiFile
import midi
import os
from fnmatch import fnmatch
import pdb

def isValidMidiTrack(track):
    if track.length == 0:
        return False
    if track.polyphonicPercentage() > 0.15:
        return False
    if track.uniqueNotes() < 4:
        return False
    return True

def filterMidiFiles(sourceDir, targetDir):
    for dirpath, dirnames, filenames in os.walk(sourceDir):
        for filename in [f for f in filenames if fnmatch(f, '*.mid')]:
            try:
                mid = MidiFile(os.path.join(dirpath,filename))
            except:
                print('Cannot read file \"{}\"'.format(os.path.join(dirpath,filename)))
                continue
            timeSignatures = midi.getMidiTimeSignature(mid)
            tempos = midi.getMidiTempo(mid)
            if len(timeSignatures) > 1:
                print('Midi contains multiple time signatures: \"{}\"'.format(os.path.join(dirpath,filename)))
                continue
            tempo = 500000
            timeSignature = (4,4,24,8)
            if len(tempos) > 0:
                tempo = tempos[0]
            if len(timeSignatures) > 0:
                timeSignature = timeSignatures[0]
            for trackNum in range(len(mid.tracks)):
                track = midi.makeTrackFromMidi(mid, trackNum)
                if isValidMidiTrack(track):
                    trackMid = midi.makeMidiFromTrack(track, mid.ticks_per_beat, tempo, timeSignature)
                    trackMidName = filename[0:-4] + "-" + str(trackNum) + ".mid"
                    trackMid.save(os.path.join(targetDir,trackMidName))
                            


# -*- coding: utf-8 -*-

from mido import MidiFile
import midi
import os
from fnmatch import fnmatch

def isValidMidiTrack(track):
    if track.length == 0:
        return False
    if not track.isMonophonic():
        return False
    return True

def filterMidiFiles(sourceDir, targetDir):
    for dirpath, dirnames, filenames in os.walk(sourceDir):
        for filename in [f for f in filenames if fnmatch(f, '*.mid')]:
            mid = MidiFile(os.path.join(dirpath,filename))
            for trackNum in range(len(mid.tracks)):
                track = midi.makeTrackFromMidi(mid, trackNum)
                if isValidMidiTrack(track):
                    trackMid = midi.makeMidiFromTrack(track, mid.ticks_per_beat)
                    trackMidName = filename[0:-4] + "-" + str(trackNum) + ".mid"
                    trackMid.save(os.path.join(targetDir,trackMidName))


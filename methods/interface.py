# -*- coding: utf-8 -*-
"""
Contains functions for input/output of data with the AI
"""

from mido import MidiFile
from os import listdir
from os.path import isfile, join
import midi
import rhythm_melody as rm
import pdb

def loadMidis(path):
    midis = [MidiFile(join(path, m)) for m in listdir(path) if isfile(join(path, m)) and m[-4:]=='.mid']
    return midis

def loadMidisAndTrainGenerator(path, hiddenStates, hiddenLayer, netEpochs, barLen, barCount, clusterCount, hmmIters=1000):
    midis = loadMidis(path)
    tracks = [midi.makeTrackFromMidi(m,0) for m in midis]
    trackDS = rm.TrackDataSet(tracks)
    generator = rm.MelodyGenerator(hiddenStates, hiddenLayer, barLen, barCount, clusterCount, hmmIters=hmmIters)
    generator.trainTimed(netEpochs, trackDS)
    return generator

def loadMidisAndGenerate(path, generator):
    midis = loadMidis(path)
    tracks = [midi.makeTrackFromMidi(m,0) for m in midis]
    generated = [generator.generateBar(t) for t in tracks]
    trackEndings = [rm.makeTrackFromRhythmMelody(r,m,6) for r,m in generated]
    return trackEndings
    

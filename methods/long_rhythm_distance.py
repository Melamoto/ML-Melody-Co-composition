# -*- coding: utf-8 -*-
"""
A hamming-distance-based model for predicting long term rhythmic patterns
"""
from rhythm_hmm import Rhythm
import math
import numpy as np

class StructuredRhythm(Rhythm):
    
    def __init__(self, ticksPerBar):
        super().__init__()
        self.ticksPerBar = ticksPerBar
    
    def bars(self):
        return math.ceil(len(self.timesteps)/self.ticksPerBar)

def makeTrackStructuredRhythm(track, ticksPerBar):
    assert track.isMonophonic(), "Only monophonic tracks can be enscribed"
    rhythm = StructuredRhythm(ticksPerBar)
    rhythm.timesteps = [0]*track.length
    noteStart = 0
    noteEnd = 0
    n = -1
    for t in range(track.length):
        if noteEnd <= t:
            n = n + 1
            noteStart = track.notes[n].start
            noteEnd = track.notes[n].start + track.notes[n].duration
        if t == noteStart:
            rhythm.timesteps[t] = 1
        elif noteStart < t and t < noteEnd:
            rhythm.timesteps[t] = 2
    return rhythm
    
def distance(sRhythm, barA, barB):
    tickA = sRhythm.ticksPerBar * barA
    tickB = sRhythm.ticksPerBar * barB
    d = 0
    for i in range(sRhythm.ticksPerBar):
        if sRhythm.timesteps[tickA+i] != sRhythm.timesteps[tickB+i]:
            d = d + 1
    return d
    
def alphaDist(sRhythm, barA, barB):
    greater = barB
    lesser = barA
    if barA > barB:
        greater = barA
        lesser = barB
    alpha = math.inf
    for i in range(lesser):
        iAlpha = distance(sRhythm, lesser, i) + distance(sRhythm, greater, i)
        if iAlpha < alpha:
            alpha = iAlpha
    return alpha
    
def betaDist(sRhythm, barA, barB):
    greater = barB
    lesser = barA
    if barA > barB:
        greater = barA
        lesser = barB
    beta = -math.inf
    for i in range(lesser):
        iBeta = abs(distance(sRhythm, lesser, i) - distance(sRhythm, greater, i))
        if iBeta > beta:
            beta = iBeta
    return beta

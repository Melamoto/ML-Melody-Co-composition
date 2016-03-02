# -*- coding: utf-8 -*-
"""
An HMM for predicting rhythmic sequences in music
"""
from hmmlearn.hmm import MultinomialHMM
import numpy as np

class Rhythm:
    
    def __init__(self):
        self.timesteps = np.array([])

    def addTimestep(self, note):
        self.timesteps = np.append(self.timesteps, note).astype(np.int32)
            
    def length(self):
        return len(self.timesteps)

def makeTrackRhythm(track):
    assert track.isMonophonic(), "Only monophonic tracks can be enscribed"
    rhythm = Rhythm()
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

def makeRhythmSamples(rhythms):
    samples = np.array([]).astype(np.int32)
    lengths = np.array([]).astype(np.int32)
    for r in rhythms:
        samples = np.concatenate((samples, r.timesteps))
        lengths = np.append(lengths, len(r.timesteps))
    samples = samples.reshape(-1,1)
    return (samples,lengths)

def buildHMM(num_states):
    model = MultinomialHMM(n_components=num_states, n_iter=1000)
    return model



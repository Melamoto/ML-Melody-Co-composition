# -*- coding: utf-8 -*-
"""
Combines the existing melody and rhythm processing methods to form complete
melody processing
"""

import rhythm_hmm as rh
import todd_ann as mel
import numpy as np
import midi

class TrackDataSet:
    
    def __init__(self,tracks):
        rhythms = [None]*len(tracks)
        melodies = [None]*len(tracks)
        mel.planCount = 1
        for i,t in enumerate(tracks):
            rhythms[i] = rh.makeTrackRhythm(t)
            melodies[i] = mel.makeTrackMelody(t,0)
        (self.rhythmSamps,self.rhythmLens) = rh.makeRhythmSamples(rhythms)
        self.melodyDS = mel.makeMelodyDataSet(melodies)
        
class MelodyGenerator:
    
    def __init__(self, stateCount, layerSize):
        self.net = mel.buildToddNetwork(layerSize)
        self.hmm = rh.buildHMM(stateCount)
        self.stateCount = stateCount
        
    def train(self, epochs, ds):
        mel.trainNetwork(self.net, ds.melodyDS, epochs)
        self.hmm.fit(ds.rhythmSamps, ds.rhythmLens)
    
    def generate(self, track, timeCount):
        # Format data for prediction
        rhythm = rh.makeTrackRhythm(track)
        melody = mel.makeTrackMelody(track,0)
        (rhythmSamps,rhythmLens) = rh.makeRhythmSamples([rhythm])
        melodyDS = mel.makeMelodyDataSet([melody])
        # Generate notes
        startState = self.hmm.predict(rhythmSamps)[-1]
        startProbs = [0]*self.stateCount
        startProbs[startState] = 1.0
        tempProbs = self.hmm.startprob_
        self.hmm.startprob_ = startProbs
        rhythmOut = np.concatenate(self.hmm.sample(timeCount)[0])
        self.net.reset()
        self.net.activateOnDataset(melodyDS)
        pitchOut = mel.getNextPitches(self.net, melody.pitches[-1],
                                      rhythm.timesteps[-1], rhythmOut)
        # Return
        self.hmm.startprob_ = tempProbs
        return (rhythmOut,pitchOut)
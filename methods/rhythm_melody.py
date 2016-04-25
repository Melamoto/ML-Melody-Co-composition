# -*- coding: utf-8 -*-
"""
Combines the existing melody and rhythm processing methods to form complete
melody processing
"""

import rhythm_hmm as rh
import long_rhythm_distance as lrd
import todd_ann as mel
import numpy as np
import midi
import time
from copy import deepcopy
import pdb
import pickle

# Temp
mel.planCount = 1

class TrackDataSet:
    
    def __init__(self,tracks):
        rhythms = [None]*len(tracks)
        melodies = [None]*len(tracks)
        mel.planCount = 1
        for i,t in enumerate(tracks):
            rhythms[i] = rh.makeTrackRhythm(t)
            melodies[i] = mel.makeTrackMelody(t,0)
        (self.rhythmSamps,self.rhythmLens) = rh.makeRhythmSamples(rhythms)
        self.rhythmTimesteps = [r.timesteps for r in rhythms]
        self.melodyDS = mel.makeMelodyDataSet(melodies)
        
class MelodyGenerator:
    
    def __init__(self, stateCount, layerSize, barLen, barCount, clusterCount, hmmIters=1000,):
        self.net = mel.buildToddNetwork(layerSize)
        self.hmm = rh.buildHMM(stateCount, n_iter=hmmIters, tol=0.00001)
        self.rdm = lrd.RhythmDistanceModel(barLen, barCount, clusterCount)
        self.stateCount = stateCount
        self.distTheta = []
        self.barLen = barLen
        self.barCount = barCount
        
    def train(self, epochs, trackDS):
        mel.trainNetwork(self.net, trackDS.melodyDS, epochs)
        bestHMM = self.hmm
        bestScore = 0
        for i in range(20):
            nextHMM = deepcopy(self.hmm)
            nextHMM.fit(trackDS.rhythmSamps, trackDS.rhythmLens)
            nextScore = nextHMM.score(trackDS.rhythmSamps, trackDS.rhythmLens)
            if nextScore > bestScore:
                bestHMM = nextHMM
                bestScore = nextScore
        self.rdm.train(trackDS.rhythmTimesteps)
        self.hmm = bestHMM
        
    def trainTimed(self, epochs, ds):
        start = time.clock()
        self.rdm.train(ds.rhythmTimesteps)
        rdm = time.clock()
        print('RDM: {}'.format(rdm-start))
        mel.trainNetwork(self.net, ds.melodyDS, epochs)
        net = time.clock()
        print('Net: {}'.format(net-rdm))
        bestHMM = self.hmm
        bestScore = -np.inf
        bestI = -1
        for i in range(10):
            nextHMM = deepcopy(self.hmm)
            nextHMM.fit(ds.rhythmSamps, ds.rhythmLens)
            nextScore = nextHMM.score(ds.rhythmSamps, ds.rhythmLens)
            # print('Score {}: {}'.format(i,nextScore))
            if nextScore > bestScore:
                bestHMM = nextHMM
                bestScore = nextScore
                bestI = i
        self.hmm = bestHMM
        hmm = time.clock()
        print('RDM: {}'.format(rdm-start))
        print('Net: {}'.format(net-rdm))
        print('HMM: {}'.format(hmm-net))
        print('Total: {}'.format(hmm-start))
        # print('Best: {} : {}'.format(bestI,bestScore))
    
    # Returns rhythm and melody of the original track + a generated bar
    def generateBar(self, track, rdmLam=4.0):
        # Format data for prediction
        rhythm = rh.makeTrackRhythm(track)
        (rhythmSamps,_) = rh.makeRhythmSamples([rhythm])
        melody = mel.makeTrackMelody(track,0)
        melodyDS = mel.makeMelodyDataSet([melody])
        # Generate notes
        rhythmOutTS = lrd.generateNextBar(self.rdm, self.hmm, rdmLam, rhythmSamps)
        #self.net.reset()
        #for sample in melodyDS.getSequenceIterator(0):
        #    self.net.activate(sample[0])
        #Whatever
        pitchOutTS = mel.getNextPitches(self.net, melody.pitches[-1], melodyDS,
                                        rhythm.timesteps[-1], rhythmOutTS)
        # Load output into classes
        rhythmOut = rh.Rhythm()
        pitchOut = mel.Melody(0)
        t = 0
        for t in range(len(rhythmOutTS)):
            rhythm.addTimestep(rhythmOutTS[t])
            newNote = (rhythmOutTS[t] == 1)
            melody.addNote(pitchOutTS[t],newNote)
        return (rhythm,melody)

    # Saves the melody generator's learned characteristics to a file to be loaded later        
    def save(self, filename):
        file = open(filename, "wb")
        pickle.dump(self, file)
        file.close()
        
def loadMelodyGenerator(filename):
    file = open(filename, 'rb')
    mg = pickle.load(file)
    file.close()
    mg.net.sorted = False
    mg.net.sortModules()
    return mg

def makeTrackFromRhythmMelody(rhythm, melody, octave):
    assert rhythm.length() == melody.length(), "Rhythm and melody must have equal lengths"
    track = midi.Track()
    t = 0
    noteTime = 0
    notePitch = 0
    noteOn = False
    while t < rhythm.length():
        if rhythm.timesteps[t] != 2 and noteOn == True:
            track.addNote(midi.Note(notePitch, noteTime, t - noteTime))
            noteOn = False
        if rhythm.timesteps[t] == 1:
            noteTime = t
            notePitch = melody.pitches[t] + octave*12
            noteOn = True
        t = t + 1
    if noteOn == True:
        track.addNote(midi.Note(notePitch, noteTime, t - noteTime))
    return track
        
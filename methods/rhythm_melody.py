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
        rhythmOutTS = np.concatenate(self.hmm.sample(timeCount)[0])
        self.net.reset()
        for sample in melodyDS.getSequenceIterator(0):
            self.net.activate(sample[0])
        pitchOutTS = mel.getNextPitches(self.net, melody.pitches[-1],
                                        rhythm.timesteps[-1], rhythmOutTS)
        # Load output into classes
        rhythmOut = rh.Rhythm()
        pitchOut = mel.Melody(0)
        t = 0
        for t in range(len(rhythmOutTS)):
            rhythmOut.addTimestep(rhythmOutTS[t])
            newNote = (rhythmOutTS[t] == 1)
            pitchOut.addNote(pitchOutTS[t],newNote)
        # Return
        self.hmm.startprob_ = tempProbs
        return (rhythmOut,pitchOut)
        
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
        
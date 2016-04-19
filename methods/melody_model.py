# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
Elman Network with Chaotic Inspiration
"""

from pybrain.structure import LinearLayer, SigmoidLayer
from pybrain.structure import RecurrentNetwork
from pybrain.structure import FullConnection, IdentityConnection
from pybrain.datasets.sequential import SequentialDataSet
from pybrain.supervised.trainers import BackpropTrainer
from scipy import dot
import operator
import midi
import numpy as np

ShortestNoteDenominator = midi.timestepsPerBeat * 2

def durationLen():
    return np.ceil(np.log2(ShortestNoteDenominator))

def sampleSize():
    return (
        7 +           # Pitch
        2 +           # Octave
        durationLen() # Duration
    )
    
def outputSize():
    return(
        7 +           # Pitch
        2 +           # Octave
        durationLen() # Duration
    )

# TODO: upgrade to use Gray Code
def getDurationString(maxLen, val):
    string = bin(val)[2:]
    assert len(string) <= maxLen, "Val must be smaller than 2^maxLen"
    paddedString = '0'*(maxLen - len(string)) + string
    return paddedString
    
# TODO: upgrade to use Gray Code
def getDurationValue(string):
    val = 0
    for c in string:
        val *= 2
        if c == '1':
            val += 1
    return val

def makeNoteSample(pitch, duration):
    sample = [int(0)] * sampleSize()
    # Pitch
    majorThirdPitch = pitch % 4
    minorThirdPitch = pitch % 3
    sample[majorThirdPitch] = 1
    sample[4+minorThirdPitch] = 1
    # Octave
    octave = np.floor(pitch / 12) - 1
    octave = max(min(octave,6),4) # Clamp octave range
    if octave == 4:
        sample[7] = 1
    elif octave == 6:
        sample[8] = 1
    # Duration
    durationString = getDurationString(durationLen(), duration)
    for i in range(len(durationString)):
        if durationString[i] == '1':
            sample[9+i] = 1
    return sample
    
def makeNoteTarget(pitch, duration):
    return makeNoteSample(pitch, duration)
    
def getPitchDurationFromSample(sample):
    majorThirdPitch = 0
    minorThirdPitch = 0
    for i in range(0,4):
        if sample[i] == 1:
            majorThirdPitch = i+1 
    for i in range(4,7):
        if sample[i] == 1:
            minorThirdPitch = i+1
    inOctavePitch = 0
    # Could use the chinese remainder theorem, might save valuable picoseconds
    for i in range(12):
        if i % 4 == majorThirdPitch and i % 3 == minorThirdPitch:
            inOctavePitch = i
    octave = 5
    if sample[7] == 1:
        octave = 4
    elif sample[8] == 1:
        octave = 6
    pitch = (octave*12) + inOctavePitch
    durationString = ''
    for i in range(9,9+durationLen()):
        durationString += str(sample[i])
    duration = getDurationValue(durationString)
    return (pitch,duration)

class Melody():
    def __init__(self):
        self.pitches = []
        self.durations = []

    def addSamples(self, dataSet):
        for s in range(len(self.pitches)-1):
            dataSet.addSample(makeNoteSample(self.pitches[s], self.durations[s]),
                              makeNoteTarget(self.pitches[s+1], self.durations[s+1]))

    def addNote(self, pitch, duration):
        self.pitches.append(pitch)
        self.durations.append(duration)
    
    def length(self):
        return len(self.pitches)

def makeTrackMelody(track,plan):
    assert track.isMonophonic(), "Only monophonic tracks can be enscribed"
    melody = Melody()
    for n in track.notes:
        melody.addNote(n.pitch,n.duration)
    return melody

def makeMelodyDataSet(melodies):
    seqDataSet = SequentialDataSet(sampleSize(), outputSize())
    for m in melodies:
        seqDataSet.newSequence()
        m.addSamples(seqDataSet)
    return seqDataSet

def buildElmanNetwork(hiddenSize):
    net = RecurrentNetwork()
    inLayer = LinearLayer(sampleSize())
    hiddenLayer = SigmoidLayer(hiddenSize)
    outLayer = SigmoidLayer(outputSize())
    net.addInputModule(inLayer)
    net.addModule(hiddenLayer)
    net.addOutputModule(outLayer)
    hiddenRecursive = IdentityConnection(hiddenLayer, hiddenLayer)
    inToHidden = FullConnection(inLayer, hiddenLayer)
    hiddenToOut = FullConnection(hiddenLayer, outLayer)
    net.addRecurrentConnection(hiddenRecursive)
    net.addConnection(inToHidden)
    net.addConnection(hiddenToOut)
    net.sortModules()
    return net
    
def trainNetwork(net, ds, epochs, momentum=0.4, weightdecay = 0.01):
    trainer = BackpropTrainer(net, dataset=ds, momentum=momentum, weightdecay=weightdecay)
    trainer.trainEpochs(epochs)

def getNextNotes(net, startPitch, pitchesDS, length):
    notes = []
    net.reset()
    for sample in pitchesDS.getSequenceIterator(0):
        net.activate(sample[0])
    lastPitch
    lastDuration
    for i in range(noteCount):
        # If a new note is being played, change the pitch
        if beats[i] == 1:
            nextSample = makeNoteSample(lastPitch,1,plan)
            out = net.activate(nextSample)
            lastPitch = max(enumerate(out),key=operator.itemgetter(1))[0]
        # If the melody is silent, use no note
        elif beats[i] == 0:
            if lastPitch != nonPitch:
                nextSample = makeNoteSample(nonPitch,0,plan)
                net.activate(nextSample)
            lastPitch = nonPitch
        notes[i] = lastPitch
    return notes
        

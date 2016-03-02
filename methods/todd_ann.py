# -*- coding: utf-8 -*-
"""
ANN based on Todd's design
"""

from pybrain.structure.connections.connection import Connection
from pybrain.structure import LinearLayer, SigmoidLayer
from pybrain.structure import RecurrentNetwork
from pybrain.structure import FullConnection, IdentityConnection
from pybrain.datasets.sequential import SequentialDataSet
from pybrain.supervised.trainers import BackpropTrainer
from scipy import dot
import operator
import midi

class WeightedPartialIdentityConnection(Connection):
    """Connection which connects the i'th element from the first module's 
    output buffer to the i'th element of the second module's input buffer, 
    multiplying the output by a weight value except for nodes greater than a 
    given index."""

    def __init__(self, weight, maxIndex, *args, **kwargs):
        Connection.__init__(self, *args, **kwargs)
        assert self.indim == self.outdim, \
               "Indim (%i) does not equal outdim (%i)" % (
               self.indim, self.outdim)
        self.weight = weight
        self.maxIndex = maxIndex

    def _forwardImplementation(self, inbuf, outbuf):
        #outbuf += dot([i*self.weight for i in inbuf],[1]*self.maxIndex + [0]*(self.indim-self.maxIndex))
        outbuf += [i*self.weight for i in inbuf]

    def _backwardImplementation(self, outerr, inerr, inbuf):
        #inerr += dot([i*self.weight for i in outerr],[1]*self.maxIndex + [0]*(self.indim-self.maxIndex))
        inerr += [i*self.weight for i in outerr]

pitchCount = 12
planCount = 0
# Value representing no pitch
nonPitch = -1

def sampleSize():
    return pitchCount + planCount + 1
    
def outputSize():
    return pitchCount

def makeNoteSample(pitch, newNote, plan):
    sample = [0] * sampleSize()
    for i in range(pitchCount):
        if i == pitch:
            sample[i] = 1
        else:
            sample[i] = 0
    sample[pitchCount] = newNote
    for i in range(planCount):
        if i == plan or plan == None:
            # If there is no plan, use all the available plans so far
            sample[i+pitchCount+1] = 1
        else:
            sample[i+pitchCount+1] = 0
    return sample
    
def makeNoteTarget(pitch):
    target = [0] * outputSize()
    for i in range(pitchCount):
        if i == pitch:
            target[i] = 1
        else:
            target[i] = 0
    return target

class Melody():
    def __init__(self,plan):
        self.pitches = []
        self.newNotes = []
        self.plan = plan

    def addSamples(self, dataSet):
        for s in range(len(self.pitches)-1):
            dataSet.addSample(makeNoteSample(self.pitches[s], self.newNotes[s],
                                             self.plan),
                              makeNoteTarget(self.pitches[s+1]))

    def addNote(self, pitch, newNote):
        self.pitches.append(pitch)
        self.newNotes.append(newNote)
    
    def length(self):
        return len(self.pitches)

def makeTrackMelody(track,plan):
    assert track.isMonophonic(), "Only monophonic tracks can be enscribed"
    melody = Melody(plan)
    melody.pitches = [nonPitch]*track.length
    melody.newNotes = [False]*track.length
    noteStart = 0
    noteEnd = 0
    n = -1
    for t in range(track.length):
        if noteEnd <= t:
            n = n + 1
            noteStart = track.notes[n].start
            noteEnd = track.notes[n].start + track.notes[n].duration
        if t == noteStart:
            melody.newNotes[t] = True
        if noteStart <= t and t < noteEnd:
            melody.pitches[t] = track.notes[n].pitch % pitchCount
    return melody

def makeMelodyDataSet(melodies):
    seqDataSet = SequentialDataSet(sampleSize(), outputSize())
    for m in melodies:
        seqDataSet.newSequence()
        m.addSamples(seqDataSet)
    return seqDataSet

def buildToddNetwork(hiddenSize):
    net = RecurrentNetwork()
    inLayer = LinearLayer(sampleSize())
    hiddenLayer = SigmoidLayer(hiddenSize)
    outLayer = SigmoidLayer(outputSize())
    net.addInputModule(inLayer)
    net.addModule(hiddenLayer)
    net.addOutputModule(outLayer)
    inRecursive = WeightedPartialIdentityConnection(0.8, pitchCount+1, inLayer, inLayer)
    inToHidden = FullConnection(inLayer, hiddenLayer)
    hiddenToOut = FullConnection(hiddenLayer, outLayer)
    net.addRecurrentConnection(inRecursive)
    net.addConnection(inToHidden)
    net.addConnection(hiddenToOut)
    net.sortModules()
    return net
    
def trainNetwork(net, ds, epochs, momentum=0.4, weightdecay = 0.01):
    trainer = BackpropTrainer(net, dataset=ds, momentum=momentum, weightdecay=weightdecay)
    trainer.trainEpochs(epochs)
    
def getNextPitches(net, startPitch, startBeat, beats, plan=0):
    noteCount = len(beats)
    notes = [0]*noteCount
    lastPitch = startPitch
    lastBeat = (startBeat == 1)
    for i in range(noteCount):
        nextSample = makeNoteSample(lastPitch,lastBeat,plan)
        out = net.activate(nextSample)
        # If the note is being sustained, do not change the pitch
        if beats[i] == 1:
            lastPitch = max(enumerate(out),key=operator.itemgetter(1))[0]
        # If the melody is silent, use no note
        elif beats[i] == 0:
            lastPitch = nonPitch
        lastBeat = (beats[i] == 1)
        notes[i] = lastPitch
    return notes
    

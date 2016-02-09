# -*- coding: utf-8 -*-
"""
ANN based on Todd's design
"""

from pybrain.structure.connections.connection import Connection
from pybrain.datasets.sequential import SequentialDataSet
from scipy import dot

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
        outbuf += dot([i*self.weight for i in inbuf],[1]*self.maxIndex + [0]*self.maxIndex)

    def _backwardImplementation(self, outerr, inerr, inbuf):
        inerr += dot([i*self.weight for i in outerr],[1]*self.maxIndex + [0]*self.maxIndex)

pitchCount = 12
planCount = 0

def sampleSize():
    return pitchCount + planCount + 1
    
def outputSize():
    return pitchCount + 1

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

class Melody():
    def __init__(self,plan):
        self.pitches = []
        self.newNotes = []
        self.plan = plan

    def addSamples(self, dataSet):
        for s in range(len(self.pitches)):
            dataSet.addSample(makeNoteSample(self.pitches[s], self.newNotes[s], self.plan))

    def addNote(self, pitch, newNote):
        self.pitches.append(pitch)
        self.newNotes.append(newNote)

def makeMelodyDataSet(melodies):
    seqDataSet = SequentialDataSet(sampleSize(), outputSize())
    for m in melodies:
        seqDataSet.newSequence()
        m.addSamples(seqDataSet)
    
    


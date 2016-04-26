# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
"""
Elman Network with Chaotic Inspiration
"""

from pybrain.structure import LinearLayer, SigmoidLayer, LSTMLayer
from pybrain.structure import RecurrentNetwork
from pybrain.structure import FullConnection, IdentityConnection
from pybrain.datasets.sequential import SequentialDataSet
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from scipy import dot
from scipy.integrate import odeint
import operator
import midi
import numpy as np
import time
import random

ShortestNoteDenominator = midi.timestepsPerBeat * 4

def durationLen():
    return int(np.ceil(np.log2(ShortestNoteDenominator)))

def sampleSize():
    return int(
        7 +             # Pitch
        2 +             # Octave
        durationLen() + # Duration
        7 +             # Inspiration
        3               # Bars
    )
    
def outputSize():
    return int(
        7 +           # Pitch
        2 +           # Octave
        durationLen() # Duration
    )

# Turns val into a string of length maxLen
def getBinaryString(maxLen, val):
    string = bin(val)[2:]
    assert len(string) <= maxLen, "Val must be at most 2^maxLen"
    paddedString = '0'*(maxLen - len(string)) + string
    return paddedString
    
# TODO: upgrade to use Gray Code
def getDurationValue(string):
    val = 0
    for c in string:
        val *= 2
        if c == '1':
            val += 1
    return val+1

def getCyclePitch(pitch):
    out = [int(0)]*7
    majorThirdPitch = pitch % 4
    minorThirdPitch = pitch % 3
    out[majorThirdPitch] = 1
    out[4+minorThirdPitch] = 1
    return out

def makeNoteSample(pitch, duration, inspirationPitch, bar):
    sample = [int(0)] * sampleSize()
    currentPos = 0
    # Pitch
    sample[currentPos:currentPos+7] = getCyclePitch(pitch)
    currentPos += 7
    # Octave
    octave = np.floor(pitch / 12) - 1
    octave = max(min(octave,6),4) # Clamp octave range
    if octave == 4:
        sample[currentPos+0] = 1
    elif octave == 6:
        sample[currentPos+1] = 1
    currentPos += 2
    # Duration
    durationString = getBinaryString(durationLen(), duration-1)
    for i in range(len(durationString)):
        if durationString[i] == '1':
            sample[currentPos+i] = 1
    currentPos += (len(durationString))
    # Inspiration
    sample[currentPos:currentPos+7] = getCyclePitch(inspirationPitch)
    currentPos += 7
    # Bars
    barString = getBinaryString(int(np.ceil(np.log2(8))), bar)
    for i in range(len(barString)):
        if barString[i] == '1':
            sample[currentPos+i] = 1
    currentPos += len(barString)
    return sample
    
def makeNoteTarget(pitch, duration):
    sample = [int(0)] * outputSize()
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
    durationString = getBinaryString(durationLen(), duration-1)
    for i in range(len(durationString)):
        if durationString[i] == '1':
            sample[9+i] = 1
    return sample
    
def getPitchDurationFromSample(sample):
    majorThirdPitch = 0
    minorThirdPitch = 0
    for i in range(0,4):
        if sample[i] == 1:
            majorThirdPitch = i 
    for i in range(4,7):
        if sample[i] == 1:
            minorThirdPitch = i-4
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
    pitch = ((octave+1)*12) + inOctavePitch
    durationString = ''
    for i in range(9,9+durationLen()):
        durationString += str(sample[i])
    duration = getDurationValue(durationString)
    return (pitch,duration)
    
def normalizeOutputSample(sample, durationThreshold=0.5, octaveThreshold=0.5):
    normalSample = [int(0)] * outputSize()
    majorThirdPitch = max(enumerate(sample[0:4]),key=operator.itemgetter(1))[0]
    minorThirdPitch = max(enumerate(sample[4:7]),key=operator.itemgetter(1))[0]
    octave = 5
    if sample[7] >= octaveThreshold or sample[8] >= octaveThreshold:
        if sample[7] > sample[8]:
            octave = 4
        else:
            octave = 6
    normalSample[majorThirdPitch] = 1
    normalSample[4+minorThirdPitch] = 1
    if octave == 4:
        normalSample[7] = 1
    elif octave == 6:
        normalSample[8] = 1
    normalSample[9:] = [int(x >= durationThreshold) for x in sample[9:]]
    return normalSample
    

class Melody():
    def __init__(self):
        self.pitches = []
        self.durations = []
        self.bars = []

    def addNote(self, pitch, duration, bar):
        self.pitches.append(pitch)
        self.durations.append(duration)
        self.bars.append(bar)
    
    def length(self):
        return len(self.pitches)

def makeMelodyFromTrack(track):
    assert track.isMonophonic(), "Only monophonic tracks can be enscribed"
    melody = Melody()
    for n in track.notes:
        bar = int(np.floor(n.start / track.barLen))
        melody.addNote(n.pitch,n.duration,bar)
    return melody

def makeTrackFromMelody(melody):
    track = midi.Track()
    totalTime = 0
    for i in range(len(melody.pitches)):
        note = midi.Note(melody.pitches[i], totalTime, melody.durations[i])
        track.addNote(note)
        totalTime += note.duration
    return track

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
    net.randomize()
    return net

def buildLstmNetwork(hiddenSize):
    net = buildNetwork(sampleSize(), hiddenSize, outputSize(), hiddenclass=LSTMLayer, outputbias=False, recurrent=True)
    net.sortModules()
    net.randomize()
    return net
    
def trainNetwork(net, ds, epochs, learningrate = 0.01, momentum=0.4, weightdecay = 0.0):
    trainer = BackpropTrainer(net,
                              dataset=ds,
                              learningrate=learningrate,
                              momentum=momentum,
                              weightdecay=weightdecay)
    trainer.trainEpochs(epochs)

def getNextNotes(net, pitchesDS, length, sequence=0):
    net.reset()
    pitches = []
    durations = []
    lastOutput = []
    normalizedOutput = []
    totalDuration = 0
    for sample in pitchesDS.getSequenceIterator(sequence):
        lastOutput = net.activate(sample[0])
    while totalDuration < length:
        normalizedOutput = normalizeOutputSample(lastOutput)
        (pitch, duration) = getPitchDurationFromSample(normalizedOutput)
        totalDuration += duration
        pitches.append(pitch)
        durations.append(duration)
        lastOutput = net.activate(normalizedOutput)
    #durations[-1] -= (totalDuration - length)
    return (pitches,durations)
    
class scale:

    def __init__(self, numOctaves, root, rootOctave, notes):#, mode, structure, toneDivision):
        self.numOctaves = numOctaves
        self.root = root
        self.rootOctave = rootOctave
        self.notes = notes
#        self.mode = mode
#        self.structure = structure
#        self.toneDivision = toneDivision
        
    def tuningFactor(self):
        return 1/2
        
    # Step 1: Scale Generation
    def getFrequencyRatioVector(self):
        ratios = []
        for i in range(int(self.numOctaves*6/self.tuningFactor())):
            if i % (6/self.tuningFactor()) in self.notes:
                ratios.append(2**(i*self.tuningFactor()/6))
        return ratios
    
    # Converts a set of note indices within the scale to their MIDI pitches
    def notesToPitches(self, notes):
        pitches = [((12*(self.rootOctave+1))
                    +self.root
                    +self.notes[n % len(self.notes)]) for n in notes]
        return pitches

majorNotes = [0,2,4,5,7,9,11]
minorNotes = [0,2,3,5,7,8,10]

NurseryScale = scale(2,0,5,majorNotes)

def lorenzDerivatives(state, t, s=10, r=28, b=8/3):
    x = state[0]
    y = state[1]
    z = state[2]
    xd = s*(y-x)
    yd = r*x - y - x*z
    zd = x*y - b*z
    return (xd,yd,zd)
    
def solveLorenzSystem(initialState, steps, start=100.0, stop=200.0):
    t = np.linspace(start, stop, steps)
    state = odeint(lorenzDerivatives, initialState, t)
    return state

def generateChaoticInspiration(scale, chaosState, chaosSteps=100):
    frv = scale.getFrequencyRatioVector()
    chaos = solveLorenzSystem(chaosState, chaosSteps)
    chaosXs = np.array([state[0] for state in chaos])
    chaosRatio = (max(frv) - min(frv)) / (max(chaosXs) - min(chaosXs))
    chaosXs *= chaosRatio       #Scale
    chaosXs += (1-min(chaosXs)) #Translate
    # chaosXs is now normalized
    noteIndices = [0]*len(chaosXs)
    for i in range(len(chaosXs)):
        bestInd = 0
        minDist = np.inf
        for j in range(len(frv)):
            newDist = abs(chaosXs[i] - frv[j])
            if newDist < minDist:
                minDist = newDist
                bestInd = j
            else:
                break
        noteIndices[i] = bestInd
    #noteIndex now has the index within the user scale of the chaotic melody
    pitches = scale.notesToPitches(noteIndices)
    return pitches

# Reseeds random
def hashInspiration(length,melody,scale=NurseryScale):
    seedVal = 0
    for i in range(len(melody.pitches)):
        seedVal += melody.pitches[i]
        seedVal *= melody.durations[i]
    random.seed(seedVal)
    xVal = random.random()*10
    yVal = random.random()*10
    zVal = random.random()*10
    random.seed()
    inspiration = generateChaoticInspiration(scale,[xVal,yVal,zVal])
    return inspiration[10:10+length]

def randomInspiration(length,melody=None,scale=NurseryScale):
    xVal = random.random()*10
    yVal = random.random()*10
    zVal = random.random()*10
    inspiration = generateChaoticInspiration(scale,[xVal,yVal,zVal])
    return inspiration[10:10+length]
    

class MelodyGenerator:
    
    def __init__(self, layerSize, barLen, barCount):
        self.net = buildElmanNetwork(layerSize)
        self.barLen = barLen
        self.barCount = barCount
        
    def train(self, epochs, tracks):
        melodies = [makeMelodyFromTrack(t) for t in tracks]
        melodyDS = makeMelodyDataSet(melodies, inspirationFunc=hashInspiration)
        # Generate chaotic inspiration and use for training
        trainNetwork(self.net, melodyDS, epochs)
        
    def trainTimed(self, epochs, tracks):
        start = time.clock()
        self.train(epochs, tracks)
        end = time.clock()
        print('Total: {}'.format(end-start))
    
    # Returns the original track + a generated bar
    def generateBar(self, track):
        # Format data for prediction
        melody = makeMelodyFromTrack(track)
        melodyDS = makeMelodyDataSet([melody])
        (pitches,durations) = getNextNotes(self.net, melodyDS, self.barLen)
        for i in range(len(pitches)):
            melody.addNote(pitches[i],durations[i])
        trackOut = makeTrackFromMelody(melody)
        return trackOut


def makeMelodyDataSet(melodies, inspirationFunc=randomInspiration, inspirationLength=8):
    seqDataSet = SequentialDataSet(sampleSize(), outputSize())
    for m in melodies:
        barCount = m.bars[-1]+1
        assert barCount <= 8, "Bar counts greater than 8 unsupported"
        inspiration = inspirationFunc(inspirationLength,m)
        seqDataSet.newSequence()
        for s in range(len(m.pitches)-1):
            seqDataSet.addSample(
                makeNoteSample(m.pitches[s], m.durations[s],
                               inspiration[s % inspirationLength], m.bars[s]),
                makeNoteTarget(m.pitches[s+1], m.durations[s+1]))
    return seqDataSet

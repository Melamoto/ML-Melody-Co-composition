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
import tkinter as tk
import tkinter.filedialog as filedialog
from tkinter.font import Font
import time
from queue import Queue, Empty
import threading

class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self,master)
        self.pack()
        self.activeThread = None
        self.eventQueue = Queue()

        self.currentMelodyGenerator = None
        self.mgStates = tk.IntVar()
        self.mgLayer = tk.IntVar()
        self.mgBarLen = tk.IntVar()
        self.mgBarCount = tk.IntVar()
        self.mgClusterCount = tk.IntVar()
        self.mgHmmEmIterations = tk.IntVar()
        
        self.trainingPath = tk.StringVar()
        self.trainingPath.set("")
        self.trainingEpochs = tk.IntVar()
        self.createWidgets()
        
        
    def createWidgets(self):
        
        self.mgSectionLabel = tk.Label(self)
        self.mgSectionLabel["text"] = "Melody Generator"
        self.mgSectionLabel["font"] = Font(size=16)
        self.mgSectionLabel.grid(row=0,column=0,columnspan=3,sticky=(tk.W,tk.S),pady=20)
        
        mgRow = 1
        
        self.mgStatesLabel = tk.Label(self)
        self.mgStatesLabel["text"] = "Hidden States"
        self.mgStatesLabel.grid(row=mgRow,column=0)
        self.mgStatesBox = tk.Entry(self)
        self.mgStatesBox["textvariable"] = self.mgStates
        self.mgStatesBox.grid(row=mgRow+1,column=0)
        
        self.mgLayerLabel = tk.Label(self)
        self.mgLayerLabel["text"] = "Hidden Layer"
        self.mgLayerLabel.grid(row=mgRow,column=1)
        self.mgLayerBox = tk.Entry(self)
        self.mgLayerBox["textvariable"] = self.mgLayer
        self.mgLayerBox.grid(row=mgRow+1,column=1)
        
        self.mgHmmEmIterationsLabel = tk.Label(self)
        self.mgHmmEmIterationsLabel["text"] = "HMM Iterations"
        self.mgHmmEmIterationsLabel.grid(row=mgRow,column=2)
        self.mgHmmEmIterationsBox = tk.Entry(self)
        self.mgHmmEmIterationsBox["textvariable"] = self.mgHmmEmIterations
        self.mgHmmEmIterationsBox.grid(row=mgRow+1,column=2)
        
        self.mgBarLenLabel = tk.Label(self)
        self.mgBarLenLabel["text"] = "Bar Length"
        self.mgBarLenLabel.grid(row=mgRow+2,column=0)
        self.mgBarLenBox = tk.Entry(self)
        self.mgBarLenBox["textvariable"] = self.mgBarLen
        self.mgBarLenBox.grid(row=mgRow+3,column=0)
        
        self.mgBarCountLabel = tk.Label(self)
        self.mgBarCountLabel["text"] = "Bar Count"
        self.mgBarCountLabel.grid(row=mgRow+2,column=1)
        self.mgBarCountBox = tk.Entry(self)
        self.mgBarCountBox["textvariable"] = self.mgBarCount
        self.mgBarCountBox.grid(row=mgRow+3,column=1)
        
        self.mgClusterCountLabel = tk.Label(self)
        self.mgClusterCountLabel["text"] = "Cluster Count"
        self.mgClusterCountLabel.grid(row=mgRow+2,column=2)
        self.mgClusterCountBox = tk.Entry(self)
        self.mgClusterCountBox["textvariable"] = self.mgClusterCount
        self.mgClusterCountBox.grid(row=mgRow+3,column=2)
        
        self.trainingSectionLabel = tk.Label(self)
        self.trainingSectionLabel["text"] = "Training"
        self.trainingSectionLabel["font"] = Font(size=16)
        self.trainingSectionLabel.grid(row=mgRow+4,column=0,columnspan=3,sticky=(tk.W,tk.S),pady=20)
        
        trainingRow = mgRow+5
        
        self.trainingPathLabel = tk.Label(self)
        self.trainingPathLabel["text"] = "Training directory: "
        self.trainingPathLabel.grid(row=trainingRow,column=0,sticky=tk.E)
        
        self.trainingPathBox = tk.Entry(self)
        self.trainingPathBox["textvariable"] = self.trainingPath
        self.trainingPathBox.grid(row=trainingRow,column=1,columnspan=1,sticky=tk.W)
        
        self.trainingPathButton = tk.Button(self)
        self.trainingPathButton["text"] = "Open..."
        self.trainingPathButton["command"] = self.selectPath
        self.trainingPathButton.grid(row=trainingRow,column=2,sticky=tk.W)
        
        self.trainingEpochsLabel = tk.Label(self)
        self.trainingEpochsLabel["text"] = "Training epochs: "
        self.trainingEpochsLabel.grid(row=trainingRow,column=3,sticky=tk.E)
        
        self.trainingEpochsBox = tk.Entry(self)
        self.trainingEpochsBox["textvariable"] = self.trainingEpochs
        self.trainingEpochsBox.grid(row=trainingRow,column=4,columnspan=2,sticky=tk.W)
        
        self.trainingButton = tk.Button(self)
        self.trainingButton["text"] = "Start Training"
        self.trainingButton["command"] = self.startTraining
        self.trainingButton["state"] = tk.DISABLED
        self.trainingButton.grid(row=trainingRow+1,column=0)
        
    def selectPath(self):
        self.trainingPath.set(filedialog.askdirectory(mustexist=True))
    
    def loadMelodyGenerator(self):
        mgFilename = filedialog.askopenfilename(filetypes=(('pickle files','.pkl'),('all files','.*')))
        if not mgFilename == '':
            self.currentMelodyGenerator = rm.loadMelodyGenerator(mgFilename)
    
    def generateMelodyGenerator(self):
        self.currentMelodyGenerator = rm.MelodyGenerator(self.mgStates.get(),
                                                         self.mgLayer.get(),
                                                         self.mgBarLen.get(),
                                                         self.mgBarCount.get(),
                                                         self.mgClusterCount.get(),
                                                         hmmIters=self.mgHmmEmIterations.get())
        
    def startTraining(self):
        self.trainingButton['state'] = tk.DISABLED
        ThreadedTrainingTask(self.eventQueue,
                             self.currentMelodyGenerator,
                             self.trainingPath.get(),
                             self.trainingEpochs.get()).start()
        self.master.after(100, self.processEventQueue)      
        
    def processEventQueue(self):
        try:
            msg = self.eventQueue.get(0)
            self.trainingButton['state'] = tk.NORMAL
            print(msg)
        except Empty:
            self.master.after(100, self.processEventQueue)

class ThreadedTrainingTask(threading.Thread):
    def __init__(self, eventQueue, mg, path, neuralNetEpochs):
        threading.Thread.__init__(self)
        self.eventQueue = eventQueue
        self.mg = mg
        self.path = path
        self.neuralNetEpochs = neuralNetEpochs
    
    def run(self):
        midis = loadMidis(self.path)
        tracks = [midi.makeTrackFromMidi(m,0) for m in midis]
        trackDS = rm.TrackDataSet(tracks)
        self.mg.trainTimed(self.neuralNetEpochs, trackDS)
        self.eventQueue.put("Training complete!")
        

def loadMidis(path):
    midis = [MidiFile(join(path, m)) for m in listdir(path) if isfile(join(path, m)) and m[-4:]=='.mid']
    return midis

def loadMidisAndTrainGenerator(path, hiddenStates, hiddenLayer, netEpochs,
                               barLen, barCount, clusterCount, hmmIters=1000,
                               filename=None):
    midis = loadMidis(path)
    tracks = [midi.makeTrackFromMidi(m,0) for m in midis]
    trackDS = rm.TrackDataSet(tracks)
    generator = rm.MelodyGenerator(hiddenStates, hiddenLayer, barLen, barCount, clusterCount, hmmIters=hmmIters)
    generator.trainTimed(netEpochs, trackDS)
    if not (filename is None):
        generator.save(filename)
    return generator

def loadMidisAndGenerate(path, generator):
    midis = loadMidis(path)
    tracks = [midi.makeTrackFromMidi(m,0) for m in midis]
    generated = [generator.generateBar(t) for t in tracks]
    trackEndings = [rm.makeTrackFromRhythmMelody(r,m,6) for r,m in generated]
    return trackEndings

# Takes a set of bars to overwrite in the original melodies
def loadMidisAndGenerateBars(path, generator, bars):
    midis = loadMidis(path)
    for b in bars:
        assert b < generator.rdm.barCount, "Invalid bar count"
    tracks = [midi.makeTrackFromMidi(m,0) for m in midis]
    generated = []
    for t in tracks:
        startBar = 0
        endBar = 0
        totalTrack = midi.Track()
        while startBar < generator.rdm.barCount:
            if startBar in bars:
                (genRhy,genMel) = generator.generateBar(totalTrack)
                totalTrack = rm.makeTrackFromRhythmMelody(genRhy,genMel,6)
                startBar += 1
            else:
                endBar = startBar+1
                while (not endBar in bars) and (endBar < generator.rdm.barCount):
                    endBar += 1
                (_,trackSeg) = midi.splitTrack(t, generator.rdm.barLen*startBar)
                (trackSeg,_) = midi.splitTrack(trackSeg, generator.rdm.barLen*endBar)
                totalTrack = midi.concatenateTracks([totalTrack,trackSeg])
                startBar = endBar
            if totalTrack.length != generator.rdm.barCount*startBar:
                pdb.set_trace()
        generated.append(totalTrack)
    return generated
    
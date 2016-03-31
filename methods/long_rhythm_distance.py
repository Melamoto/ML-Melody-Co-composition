# -*- coding: utf-8 -*-
"""
A hamming-distance-based model for predicting long term rhythmic patterns
"""
from rhythm_hmm import Rhythm
import math
import numpy as np
from scipy.cluster.vq import vq, kmeans, whiten
from scipy.stats import binom

class StructuredRhythm(Rhythm):
    
    def __init__(self, ticksPerBar):
        super().__init__()
        self.ticksPerBar = ticksPerBar
    
    def bars(self):
        return math.ceil(len(self.timesteps)/self.ticksPerBar)

class RhythmDistanceModel:
    
    def __init__(self, partitions, rhyLen, barLen, clusterCount):
        self.partitions = partitions
        self.rhyLen = rhyLen
        self.barLen = barLen
        self.weights = np.zeros((rhyLen,rhyLen,clusterCount))
        self.probs = np.zeros((rhyLen,rhyLen,clusterCount))
        self.clusterCount = clusterCount
        
    def train(self, srhythms, convergence=0.01, maxIters=1000):
        for rhy in srhythms:
            assert rhy.bars() == self.rhyLen, "Rhythms must have correct number of measures"
            assert rhy.ticksPerBar == self.barLen, "Rhythm measures must have correct length"
        for i in range(self.rhyLen-1):
            for j in range(i+1,self.rhyLen):
                # Initialise parameter estimates
                ijDS = np.zeros(len(srhythms))
                for r in range(len(srhythms)):
                    dist = distance(srhythms[r], i, j)
                    a = alphaDist(srhythms[r], i, j)
                    b = betaDist(srhythms[r], i, j)
                    if a - b == 0:
                       ijDS[r] = 0
                    else:
                       ijDS[r] = (dist - b)/(a - b)
                centroids = kmeans(ijDS, self.clusterCount)[0]
                code = vq(ijDS, centroids)[0]
                for k in range(self.clusterCount):
                    n = sum(c == k for c in code)
                    self.weights[i][j][k] = n / len(ijDS)
                    self.probs[i][j][k] = centroids[k]
                # Use iterative EM to refine parameters
                converged = False
                iters = 0
                while (not converged) and (iters < maxIters):
                    converged = True
                    iters += 1
                    clusterProbs = np.zeros((len(self.clusterCount),len(srhythms)))
                    for k in range(self.clusterCount):
                        for r in range(len(srhythms)):
                            dist = distance(srhythms[r], i, j)
                            a = alphaDist(srhythms[r], i, j)
                            b = betaDist(srhythms[r], i, j)
                            clusterProbs[k][r] = self.weights[i][j][k] * binomialDistanceProb(dist,a,b,self.probs[i][j][k])
                    # Normalize cluster probabilities s.t. the total prob 
                    # across clusters for a given rhythm is 1
                    np.divide(clusterProbs, np.sum(clusterProbs,0))
                    for k in range(self.clusterCount):
                        numerator = 0.0
                        denominator = 0.0
                        for r in range(len(srhythms)):
                            dist = distance(srhythms[r], i, j)
                            a = alphaDist(srhythms[r], i, j)
                            b = betaDist(srhythms[r], i, j)
                            numerator += (dist - b) * clusterProbs[k][r]
                            denominator += (a - b) * clusterProbs[k][r]
                        oldProb = self.probs[i][j][k]
                        oldWeight = self.weights[i][j][k]
                        self.probs[i][j][k] = numerator/denominator
                        self.weights[i][j][k] = np.sum(clusterProbs[k])/len(srhythms)
                        if abs(self.probs[i][j][k]-oldProb)/self.probs[i][j][k] > convergence:
                            converged = False
                        if abs(self.weights[i][j][k]-oldWeight)/self.weights[i][j][k] > convergence:
                            converged = False
        return 0

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

def binomialDistanceProb(dist, alpha, beta, prob):
    if alpha - beta == 0:
        return 1
    return binom.pmf(dist, alpha - beta, prob)
        

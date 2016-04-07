# -*- coding: utf-8 -*-
"""
A hamming-distance-based model for predicting long term rhythmic patterns
"""
from rhythm_hmm import Rhythm, makeRhythmSamples
import math
import numpy as np
from scipy.cluster.vq import vq, kmeans
from scipy.stats import binom

class StructuredRhythm(Rhythm):
    
    def __init__(self, ticksPerBar):
        super().__init__()
        self.ticksPerBar = ticksPerBar
    
    def bars(self):
        return math.ceil(len(self.timesteps)/self.ticksPerBar)

class RhythmDistanceModel:
    
    def __init__(self, rhyLen, barLen, clusterCount, partitions=None):
        self.partitions = partitions
        self.rhyLen = rhyLen
        self.barLen = barLen
        self.weights = np.zeros((rhyLen,rhyLen,clusterCount))
        self.probs = np.zeros((rhyLen,rhyLen,clusterCount))
        self.clusterCount = clusterCount
        self.converged = False
        
    def train(self, rhythms, convergence=0.00001, maxIters=1000):
        for rhy in rhythms:
            assert len(rhy) == self.rhyLen*self.barLen, "Rhythms must correct number of measures and length"
        for i in range(self.rhyLen-1):
            for j in range(i+1,self.rhyLen):
                # TODO: Clean these variables up
                dists = [distance(rhythms[r], i, j, self.barLen) for r in rhythms]
                alphas = [alphaDist(rhythms[r], i, j, self.barLen) for r in rhythms]
                betas = [betaDist(rhythms[r], i, j, self.barLen) for r in rhythms]
                # Initialise parameter estimates
                ijDS = np.zeros(len(rhythms))
                for r in range(len(rhythms)):
                    dist = distance(rhythms[r], i, j, self.barLen)
                    a = alphaDist(rhythms[r], i, j, self.barLen)
                    b = betaDist(rhythms[r], i, j, self.barLen)
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
                    clusterProbs = np.zeros((len(self.clusterCount),len(rhythms)))
                    for k in range(self.clusterCount):
                        for r in range(len(rhythms)):
                            dist = distance(rhythms[r], i, j, self.barLen)
                            a = alphaDist(rhythms[r], i, j, self.barLen)
                            b = betaDist(rhythms[r], i, j, self.barLen)
                            """
                            TODO: Not sure about using this; the paper says to
                            use dist but I think it's a typo - it doesn't make
                            that much sense otherwise
                            """
                            sigma = dist - b
                            clusterProbs[k][r] = self.weights[i][j][k] * binomialDistanceProb(sigma,a,b,self.probs[i][j][k])
                    # Normalize cluster probabilities s.t. the total prob 
                    # across clusters for a given rhythm is 1
                    np.divide(clusterProbs, np.sum(clusterProbs,0))
                    for k in range(self.clusterCount):
                        numerator = 0.0
                        denominator = 0.0
                        for r in range(len(rhythms)):
                            dist = distance(rhythms[r], i, j, self.barLen)
                            a = alphaDist(rhythms[r], i, j, self.barLen)
                            b = betaDist(rhythms[r], i, j, self.barLen)
                            numerator += (dist - b) * clusterProbs[k][r]
                            denominator += (a - b) * clusterProbs[k][r]
                        oldProb = self.probs[i][j][k]
                        oldWeight = self.weights[i][j][k]
                        self.probs[i][j][k] = numerator/denominator
                        self.weights[i][j][k] = np.sum(clusterProbs[k])/len(rhythms)
                        if abs(self.probs[i][j][k]-oldProb)/self.probs[i][j][k] > convergence:
                            converged = False
                        if abs(self.weights[i][j][k]-oldWeight)/self.weights[i][j][k] > convergence:
                            converged = False
        self.converged = converged

    # Returns a log probability of "bar" succeeding "rhythm" according to this
    # model
    def score(self, rhythm, bar):
        assert len(rhythm) % self.barLen == 0, "Rhythm length must be divisible by bar length"
        assert len(bar) == self.barLen, "Input bar has incorrect length"
        totalProb = 0.0
        combinedRhythm = rhythm + bar
        j = (len(rhythm) / self.barLen)
        for i in range(j):
            dist = distance(combinedRhythm, i, j)
            alpha = alphaDist(combinedRhythm, i, j)
            beta = betaDist(combinedRhythm, i, j)
            sigma = dist - beta
            iProb = 0.0
            for k in range(self.clusterCount):
                iProb += self.weights[i][j][k] * binomialDistanceProb(sigma,alpha,beta,self.probs[i][j][k])
            totalProb += np.log(iProb)
        return totalProb
        

def generateNextBar(rdm, hmm, lam, rhythm, partitions=None):
    assert rhythm.length() % rdm.barLen == 0, "Rhythm length must be divisible by bar length"
    assert rhythm.length() < rdm.barLen * rdm.rhyLen, "Rhythm length must be less than distance model maximum"
    (rhythmSamps,rhythmLens) = makeRhythmSamples([rhythm])
    # Generate notes
    startStateProbs = hmm.predict_proba(rhythmSamps)[-1]
    tempProbs = hmm.startprob_
    hmm.startprob_ = startStateProbs
    barOut = np.concatenate(hmm.sample(rdm.barLen)[0])
    end = False
    while end == False:
        end = True
        for j in range(rdm.barLen):
            startVal = barOut[j]
            bestVal = 0
            bestScore = -np.inf
            for newVal in range(3):
                newBar = barOut
                newBar[j] = newVal
                hmmScore = hmm.score(newBar)
                distScore = rdm.score(rhythm.timesteps, newBar)
                newScore = hmmScore + (lam * distScore)
                if newScore > bestScore:
                    bestScore = newScore
                    bestVal = newVal
            barOut[j] = bestVal
            # Converge only when no values are changed
            if bestVal != startVal:
                end = False
    hmm.startrob_ = tempProbs
    return barOut

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
    
def distance(rhythm, barA, barB, ticksPerBar):
    tickA = ticksPerBar * barA
    tickB = ticksPerBar * barB
    d = 0
    for i in range(ticksPerBar):
        if rhythm[tickA+i] != rhythm[tickB+i]:
            d = d + 1
    return d
    
def alphaDist(rhythm, barA, barB, ticksPerBar):
    greater = barB
    lesser = barA
    if barA > barB:
        greater = barA
        lesser = barB
    alpha = math.inf
    for i in range(lesser):
        iAlpha = distance(rhythm, lesser, i, ticksPerBar) + distance(rhythm, greater, i, ticksPerBar)
        if iAlpha < alpha:
            alpha = iAlpha
    return alpha
    
def betaDist(rhythm, barA, barB, ticksPerBar):
    greater = barB
    lesser = barA
    if barA > barB:
        greater = barA
        lesser = barB
    beta = -math.inf
    for i in range(lesser):
        iBeta = abs(distance(rhythm, lesser, i, ticksPerBar) - distance(rhythm, greater, i, ticksPerBar))
        if iBeta > beta:
            beta = iBeta
    return beta

def binomialDistanceProb(sigma, alpha, beta, prob):
    if alpha - beta == 0:
        if sigma == 0:
            return 1
        else:
            # TODO: This causes a gradient of 0 among "impossible" distance
            # values - making gradient ascent impossible.Fix this maybe.
            return 0
    return binom.pmf(sigma, alpha - beta, prob)
        

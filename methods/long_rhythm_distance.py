# -*- coding: utf-8 -*-
"""
A hamming-distance-based model for predicting long term rhythmic patterns
"""
from rhythm_hmm import Rhythm, makeRhythmSamples
import math
import numpy as np
from scipy.cluster.vq import vq, kmeans
from scipy.stats import binom
import pdb

class StructuredRhythm(Rhythm):
    
    def __init__(self, ticksPerBar):
        super().__init__()
        self.ticksPerBar = ticksPerBar
    
    def bars(self):
        return math.ceil(len(self.timesteps)/self.ticksPerBar)

class RhythmDistanceModel:
    
    def __init__(self, barLen, barCount, clusterCount, partitions=None):
        self.partitions = partitions
        self.barCount = barCount
        self.barLen = barLen
        self.weights = np.zeros((barCount,barCount,clusterCount))
        self.probs = np.zeros((barCount,barCount,clusterCount))
        self.clusterCount = clusterCount
        self.converged = False
        self.minimumDistanceProb = 1/(self.barLen+1)
        self.maximumDistanceProb = 1 - self.minimumDistanceProb
        
    def train(self, rhythms, convergence=0.000001, maxIters=10000):
        for rhy in rhythms:
            assert len(rhy) == self.barCount*self.barLen, "Rhythms must correct number of measures and length"
        for i in range(self.barCount-1):
            for j in range(i+1,self.barCount):
                #pdb.set_trace()
                dists = [distance(r, i, j, self.barLen) for r in rhythms]
                alphas = [alphaDist(r, i, j, self.barLen) for r in rhythms]
                betas = [betaDist(r, i, j, self.barLen) for r in rhythms]
                # Initialise parameter estimates
                ijDS = np.zeros(len(rhythms))
                for r in range(len(rhythms)):
                    if alphas[r] - betas[r] == 0:
                       ijDS[r] = 0
                    else:
                       ijDS[r] = (dists[r] - betas[r])/(alphas[r] - betas[r])
                    ijDS[r] = max(min(ijDS[r],self.maximumDistanceProb),self.minimumDistanceProb)
                centroids = kmeans(ijDS, self.clusterCount)[0]
                # TODO: Bit of a hack, but necessary in some form
                while len(centroids) < self.clusterCount:
                    centroids = np.append(centroids, centroids[-1])
                code = vq(ijDS, centroids)[0]
                for k in range(self.clusterCount):
                    n = sum(c == k for c in code)
                    self.weights[i][j][k] = n / len(rhythms)
                    self.probs[i][j][k] = centroids[k]
                # Use iterative EM to refine parameters
                converged = False
                iters = 0
                while (not converged) and (iters < maxIters):
                    converged = True
                    iters += 1
                    clusterProbs = np.zeros((self.clusterCount,len(rhythms)))
                    for k in range(self.clusterCount):
                        for r in range(len(rhythms)):
                            """
                            TODO: Not sure about using this; the paper says to
                            use dist but I think it's a typo - it doesn't make
                            that much sense otherwise
                            """
                            sigma = dists[r] - betas[r]
                            clusterProbs[k][r] = (
                                self.weights[i][j][k] *
                                self.gradientBinomialDistanceProb(sigma,alphas[r],betas[r],self.probs[i][j][k]))
                    # Normalize cluster probabilities s.t. the total prob 
                    # across clusters for a given rhythm is 1
                    np.divide(clusterProbs, np.sum(clusterProbs,0))
                    for k in range(self.clusterCount):
                        numerator = 0.0
                        denominator = 0.0
                        for r in range(len(rhythms)):
                            numerator += (dists[r] - betas[r]) * clusterProbs[k][r]
                            denominator += (alphas[r] - betas[r]) * clusterProbs[k][r]
                        oldProb = self.probs[i][j][k]
                        oldWeight = self.weights[i][j][k]
                        if denominator == 0:
                            self.probs[i][j][k] = 0
                        else:
                            self.probs[i][j][k] = numerator/denominator
                        self.probs[i][j][k] = max(min(
                            self.probs[i][j][k],
                            self.maximumDistanceProb),
                            self.minimumDistanceProb)
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
        combinedRhythm = np.concatenate([rhythm, bar])
        j = int(len(rhythm) / self.barLen)
        for i in range(j):
            dist = distance(combinedRhythm, i, j, self.barLen)
            alpha = alphaDist(combinedRhythm, i, j, self.barLen)
            beta = betaDist(combinedRhythm, i, j, self.barLen)
            sigma = dist - beta
            iProb = 0.0
            for k in range(self.clusterCount):
                iProb += self.weights[i][j][k] * self.gradientBinomialDistanceProb(sigma,alpha,beta,self.probs[i][j][k])
            totalProb += np.log(iProb)
        return totalProb
    
    # As binomialDistanceProb below, but adds a gradient to impossible distance
    # value probabilities, so that all probabilities are non-zero and "more 
    # impossible" values have lower probability
    def gradientBinomialDistanceProb(self, sigma, alpha, beta, prob):
        if alpha - beta == 0:
            if sigma == 0:
                return 1
            else:
                return self.minimumDistanceProb**(1+sigma)
        return max(min(
            binom.pmf(sigma, alpha - beta, prob),
            self.maximumDistanceProb),
            self.minimumDistanceProb)
        

def generateNextBar(rdm, hmm, lam, rhythm, partitions=None):
    assert len(rhythm) % rdm.barLen == 0, "Rhythm length must be divisible by bar length"
    assert len(rhythm) < rdm.barLen * rdm.barCount, "Rhythm length must be less than distance model maximum"
    # Generate notes
    # TODO: Use predict_proba instead to achieve a more accurate range of results
    #startState = hmm.predict(rhythm)[-1]
    #startStateProbs = [0]*len(hmm.startprob_)
    #startStateProbs[startState] = 1.0
    startStateProbs = hmm.predict_proba(rhythm)[-1]
    tempProbs = hmm.startprob_
    hmm.startprob_ = startStateProbs
    startSymbol = hmm.sample(1)[0][0]
    barOut = np.concatenate(hmm.sample(rdm.barLen+1)[0])[1:]
    rhythmSteps = np.concatenate(rhythm)
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
                hmmScore = hmm.score(np.concatenate([startSymbol,newBar]).reshape(-1,1))
                distScore = rdm.score(rhythmSteps, newBar)
                newScore = hmmScore + (lam * distScore)
                if newScore > bestScore:
                    bestScore = newScore
                    bestVal = newVal
            barOut[j] = bestVal
            # Converge only when no values are changed
            if bestVal != startVal:
                end = False
    hmm.startprob_ = tempProbs
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
    if lesser == 0:
        return distance(rhythm, barA, barB, ticksPerBar)
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
    if lesser == 0:
        return distance(rhythm, barA, barB, ticksPerBar)
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
            # This causes a gradient of 0 among "impossible" distance
            # values - making gradient ascent impossible. For cases where 
            # gradient ascent is needed, use gradientBinomialDistanceProb
            return 0
    return binom.pmf(sigma, alpha - beta, prob)
        

# -*- coding: utf-8 -*-

from deap import base, creator, tools
import random
import midi

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

def initPopulation(pcls, indInit):
    pass

def mutateMelody(mel):
    mergeProb = 0.1
    splitProb = mergeProb + 0.15
    transposeProb = splitProb + 0.25
    reversalProb = transposeProb + 0.25
    rotateProb = reversalProb + 0.25

    transposeMax = 7
    
    mutationChoice = random.random()
    if mutationChoice < mergeProb:
        if len(mel) > 1:
            start = random.randrange(0,len(mel)-1)
            mel[start].duration += mel[start+1].duration
            del mel[start+1]
    elif mutationChoice < splitProb:
        start = random.randrange(0,len(mel))
        if mel[start].duration > 1:
            startLen = random.randrange(1,mel[start].duration)
            nextLen = mel[start].duration - startLen
            mel[start].duration = startLen
            mel.insert(start+1, midi.Note(mel[start].pitch,
                                          mel[start].start + startLen,
                                          nextLen))
    elif mutationChoice < transposeProb:
        start = random.randrange(0,len(mel))
        end = random.randrange(start,len(mel))
        transpose = random.randint(-transposeMax,transposeMax)
        for i in range(start,end+1):
            mel[i].pitch += transpose
        pass
    elif mutationChoice < reversalProb:
        if len(mel) > 1:
            start = random.randrange(0,len(mel)-1)
            end = random.randrange(start+1,len(mel))
            startTime = mel[start].start
            endTime = mel[end].start + mel[end].duration
            reverseSlice = mel[start:end+1]
            reverseSlice.reverse()
            mel[start:end+1] = reverseSlice
            for i in range(start,end+1):
                mel[i].start = startTime + (endTime - (mel[i].start+mel[i].duration))
    elif mutationChoice < rotateProb:
        if len(mel) > 1:
            start = random.randrange(0,len(mel)-1)
            end = random.randrange(start+1,len(mel))
            startTime = mel[start].start
            rotation = random.randint(1,end-start)
            for i in range(rotation):
                last = mel.pop(end)
                mel.insert(start,last)
                mel[start].start = startTime
                for j in range(start+1,end+1):
                    mel[j].start += mel[start].duration
                    

def crossoverMelody(melA, melB):
    pass


toolbox = base.Toolbox()

toolbox.register("populationGuess", initPopulation, list, creator.Individual)

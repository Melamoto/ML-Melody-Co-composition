---
layout: post
title:  "First Prototype"
date:   2016-02-09 21:00:00 +0000
categories: progress update planning
---
### Summary

This post discusses the methods used so far in the creation of the first 
prototype melody completion. A summary of the key points of this post are 
given here:

The first method I am using is an artificial neural network designed by Peter 
M. Todd. The network is recurrent and attempts to produce successive notes 
based on the "context" of the previously played notes. I have started an 
implementation of this in Python, using the [PyBrain](http://pybrain.org/) 
library. This has mostly gone smoothly but it has taken time to get up to 
speed with the API, further marred by minor peculiarities of the network's 
design that required a deeper understanding of the library to get working. 
The network also only deals with monophonic melodies, which is not an issue 
for testing purposes at this point but may slightly increase the difficulty of 
finding good music data.

### Method

As mentioned in the previous post, the method being used for this first 
attempt will be an artifical neural network (ANN). This particular model is 
based off of the algorithm described in [*A Connectionist Approach to 
Algorithmic Composition*](http://www.indiana.edu/~abcwest/pmwiki/pdf/todd.compmusic.1989.pdf) by Peter M. Todd, 1989.

This particular model uses a recurrent network model, in which the input layer 
is fully connected to the hidden layer, and the hidden to the output. The 
input layer is divided up into two parts - the context and the plan. The 
context is a set of notes representative of pitch, with one node being 
dedicated to each possible pitch value. Notably the design uses absolute pitch 
instead of relative pitch, to avoid issues with the melody straying off-key. 
Each output node corresponds to a pitch as well, with the output values being 
used to determine the next note played. Each output node has a recurrent 
connection to the corresponding context node with weight 1, so that the note 
that is played will be used as the "context" for the next note. Each context 
node has a recurrent connection to itself, with a weight in the range (0, 1), 
allowing the network to remember the notes that have been played recently. 

### Issues

There are a few drawbacks to the method used by Todd. Most notably, the 
representation used does not allow for polyphonic melodies, due to the nature 
of the "new note" node - as different notes may play at overlapping times in 
polyphonic melodies, each pitch would need an individual "new note" node. 
While this method is not strictly infeasible, it may not be the most efficient 
or effective way to represent these melodies. The system also does not have 
any particular method for dealing with harmonization - it is quite likely to 
have a relatively low success rate at producing traditionally "good" 
harmonies. 

This also greatly restricts the availability of music files for training, as 
many of the free musical pieces that would otherwise be appropriate for the 
task contain polyphonic melodies - particularly the solo piano pieces 
suggested previously. This may be remedied to an extent by instead finding 
MIDI music with many monophonic voices, and extracting a single voice for 
training/testing. This is likely to be possible for many orchestral pieces, 
where many instruments play monophonic melodies.

### Progress

I have been making slow (but steady) progress with the implementation of this 
prototype. My implementation is written in Python as planned, using the 
[PyBrain](http://pybrain.org/) library for the neural network implementation. 
The current state of the implementation is mostly complete - aside from some 
issues (mentioned below) the network is more or less complete. It has not been 
tested at all however, and is my own first time creating anything like this, 
so it would be reasonable to assume it may take another day or two of work to 
finish. 

Aside from the issues in the section above, there have been a few details I 
have been spending my time on. Most significantly, I have had to delve 
somewhat into the details of PyBrain's code beyond the simple, standard usage 
APIs. The reason for this is that some of the particulars of Todd's network 
(most of all the separation of the input layer into two distinct sections with 
different properties) are ill-supported by the library by default, as far as I 
have been able to tell from the API. It is possible I have overlooked 
something, but I have not been able to find anything useful so far. Instead, I 
have implemented some classes of my own to handle this specific case. This is 
not a particularly complicated process - indeed, the PyBrain website includes 
explicit and simple instructions for doing so. However, to do this I first had 
to spend some time studying the API to learn how to make what I needed. For 
now at least I don't consider this wasted effort, as in doing so I also 
learned more about the actual operation of neural networks, which will likely 
be useful later.

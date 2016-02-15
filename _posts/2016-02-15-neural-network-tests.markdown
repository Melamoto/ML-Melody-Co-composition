---
layout: post
title:  "Testing the neural network"
date:   2016-02-15 21:00:00 +0000
categories: progress update 
---
### Testing parameters

To test the effectiveness of the neural network built with various parameters, 
I prepared a set of melodies and corresponding completion tasks.

Each one of the melodies used can be categorised as one of the following (with 
corresponding examples):

* Simple repetitive melodies
* Complex repetitive melodies
* Non-repeating melodies
* Real-world melodies

These categories are ordered from least to most complex, although this measure 
does not strictly capture the ANN's actual performance. Each melody used 
between 8 and 32 time slices.

In addition to testing the neural network against singular melodies, I also had 
the ANN trained with several melodies simultaneously, using the *plan units* to 
track the source melody. Each trial used between 1 and 4 different melodies.

The parameters of the ANN modified throughout the tests included:

* No. of hidden neurons
* Learning rate
* Momentum
* Epochs trained
	
Parameters in this context may have a number of different purposes. Some 
provide strict increases in success in exchange for greater time spent 
running/training, in this case epochs trained. Others affect the efficiency of 
the learning process, such as the learning rate and momentum. Finally, the 
number of hidden neurons produces a slightly more subtle effect; while 
increasing the size of the hidden layer technically increases the computational 
power of the neural network, it also reduces its ability to generalize. The 
larger the hidden layer, the more likely each training session is to converge 
on an exact solution to all the available data instead of extracting the 
meaningful features - causing the network to, in practice, only recite the 
learned melodies exactly instead of producing melodies that are similar but 
different. 

### Results

Due to the experimental nature of this development stage, a comprehensive set 
of results across a large domain of inputs and parameters will not be used. 
Instead, a set of useful and important results will be given, in approximate 
order of complexity.

#### Single simple repetitive melody

This particular configuration represents the absolute baseline of a functioning 
network. Therefore, the creation of a satisfactory neural network essentially 
required only a partial implementation of the Todd-model network. Perfect 
accuracy may be achieved with 1 hidden neuron and <100 training epochs.

Example: (C,C,C,C,C,C,C,C)

#### Many non-overlapping simple repetitive melodies

Compared to the previous step, the increase in difficulty is only minor. It is 
another simple test that requires the network to reccognize more than one 
separate pattern. Notable, it was sufficient to provide only a plan without an 
actual note and vice versa - proving the operationality of both the plan nodes 
and the context nodes.

Example: (C,C,C,C,C,C,C,C), (D,D,D,D,D,D,D,D), (E,E,E,E,E,E,E,E)

#### Single complex repetitive melody

These melodic patterns are similar to the above in that they require the use of 
context memory to determine the next note. However, they do not allow the use 
of a plan, providing a more thorough test of context. They were found to nr 
slightly harder than the previous challenge, requiring more training epochs.

Example: (C,D,E,D,C,D,E,D)

#### Many overlapping non-repeating melodies

This is an increase in difficulty over the previous step, as it removes the 
deterministic nature of the pattern with respect to the last note. This 
therefore tests both the plan nodes and the context node memory. Increasing the 
number of hidden neurons and training epochs was sufficient to achieve total 
success on all trials.

Example: (C,C#,D,D#,E,F,F#,G), (G,F#,F,E,D#,D,C#,C)

#### Simplified real-world melodies

These melodies can be classified simply as melodies that occur in 
human-composed music; more specifically for these tests however, these are 
melodies that contain patterns that repeat with variation. It is a fairly 
complex task to recreate these even for simple melodies, as the network must 
learn to differentiate between highly similar contexts to determine the next 
note from a given point - it may need to "look" many notes into the past to 
identify the context at a given point. The melodies were simplified at this 
stage by making each note 1 crotchet, removing rests, and replacing sustained 
notes with repeated notes.

Example: The vocal line to Beethoven's *Ode to Joy*
(E,E,F,G,G,F,E,D,C,C,D,E,E,D,D)

### Future developments

The steps documented here are an important part of development, but do not 
address the core issue at work: replicating a musical *style*, as opposed to 
replicating individual melodies. Obviously this requires a great deal more work 
than what has been covered here. However, using this set of tests as a first 
step simplifies the following step - style replication may be achieved by 
extracting relevant features from works of an artist, which is approximately 
what is happening here on a much smaller scale. Following this, my next goal 
will be to introduce more powerful generalizations; it is likely this will 
require special-case logic for harmonizations and sectional differences, as 
well as a more refined system for pattern recognition.

---
layout: post
title:  "Objectives"
date:   2016-02-06 21:00:00 +0000
categories: progress update planning
---
### Summary

This post discusses the measurable objectives of the AI being create in this 
project. A summary of the key points of this post are given here:

The objectives can be considered hierarchically, such that the top level 
objective is the goal of this project. This goal can be described as "the 
extrapolation from a small amount of musical data to produce a continuation of 
arbitrary length that is consistent in style with the original data." This is 
broken down into sub-objectives by reducing the complexity of the task. The 
dimensions of the task's complexity are given by the size of the input data, 
the size of the output data, and the relation between the input and output 
data. Due to the complexity of dealing with distant relations, the first few 
rounds of testing will be use closely related input and output data of various 
sizes. This data will be obtained by taking existing musical pieces, removing 
some elements, and having the AI attempt to complete the missing parts. This 
will be assessed primarily using human feedback. The first tests will provide 
a complete phrase with the final note removed. For each tested AI, the amount 
of content removed will be increased iteratively in repeated tests, and the AI 
will be assessed on its performance at all levels. 

### Requirements

As mentioned in the previous post, for any measurable progress to be made in 
this project there must exist a set of measurable objectives. These objectives 
should be defined in a hierarchical manner, such that each "parent" objective 
is strictly harder than each of its children. Following from this, the final 
objective (the "root") is the ultimate goal of the project - satisfying it 
would constitute completion. It is expected that the satisfaction of 
objectives will not be a boolean condition, but instead a continuous grading 
based on distance to an optimal result. These objectives will guide the entire 
development process, and so it is important that they accurately represent the 
complete problem. Depending on the difficulty of these objectives, the final 
goal may be simplified, expanded, or otherwise altered.

To determine the most reasonable set of objectives, it is useful to consider 
previous work in this area and what has been achieved. The majority of work in 
AI music composition can be divided into two categories: *imitation* of an 
existing musical style and *original* creative work. Generally speaking, the 
latter is not rigorously defined and lacks a widely accepted formalization. 
Nevertheless it can be considered separate to imitation as a process, in that 
it does not produce a musical piece strictly derived from a single selection 
of sources. This particular AI is intended to expand upon the work of the 
user, a human composer. In this sense it can be considered a form of 
imitation - with the important distinction that it has access to only a small 
volume of work from the user (potentially less than one song), but a larger 
volume of work from other sources, some of whom may be similar in style to the 
user.

### Goals

Working from this a slightly more concrete end objective can be seen: the AI 
must extrapolate from a small amount of musical data to produce a continuation 
of arbitrary length that is consistent in style with the original data. 
Putting aside concerns about the ratio of input size to output size, which 
clearly increases the difficulty of the task, there is an issue with this 
definition - namely, what exactly is meant by *consistent*.

It is generally the case that a given partial song could be completed in many 
ways by the same composer, and finding a deterministic method that accurately 
computes stylistic similarity between two different pieces presents a 
significant challenge in itself. Indeed, previous work in this area has 
generally relied on human feedback for assessment, either from observers or 
from the musician themselves. This process is costly in terms of time and 
effort required, which is likely to be a serious problem when trying to 
rapidly prototype solutions.

In this particular case however, there may be an alternative answer. As this 
particular AI is intended to continue unfinished musical pieces, it should 
also be able to approximately "recomplete" already finished pieces. This can 
be assessed by taking a piece of music, removing some information from it, and 
having the AI attempt to complete the removed info. A more successful AI will 
generally have a higher probability of returning the original piece. This 
solution also comes with a serious problem: as mentioned earlier, there may 
exist many "good" completions that the original composer could give, and so it 
stands to reason that a perfect imitation could also give these as results 
instead of the actual completion.

To overcome this, there are a few possibilities. Music could be provided by a 
composer with a set of variations, allowing any of these variations to be 
considered a valid completion by the AI. Alternatively, human feedback could 
be used to estimate a "probability" for the actual completion of the piece, 
allowing the AI's success to be judged by comparing its probability of correct 
completion with the human estimate. Both of these methods have drawbacks and 
require human intervention, but in the absence of a true comparison function 
this is unavoidable.  

### Objectives

Given the end goal described above, it is easy to consider an ideal first 
objective. The simplest case of completion possible would be one in which the 
removed information was as small as possible. This corresponds to the removal 
of a single note from an otherwise complete piece. In fact, the amount of 
information removed could be reduced even further by retaining the pitch of 
the note and removing the duration, or vice versa, and then further still by 
restricting the domain of allowed values. Early on in the project it would be 
ideal to test removing whole notes to determine the approximate success rates 
of various methods on the complete problem. Testing pitch and duration removal 
individually will certainly be useful for a more in-depth analysis however - 
as the two influence each other, it would provide some useful correlational 
data. 

As the project progresses and the AI must be tested more vigorously, it should 
be acceptable to increase the scale of information removed, reducing the data 
available to the AI and/or increasing the size of the output. This nicely 
leads up to the final objective, in which the input and output sizes are 
arbitrary.

An additional factor that must also be considered however is relation; it is 
not necessary that the existing melody and the melody to be completed are 
adjacent, within the same section, or even the same voice. The relation can 
also be considered a factor of increasing difficulty, and should be taken into 
account. This adds an entire new dimension of complexity to the AI, and is 
expected to be one of the more difficult problems to solve.

Thus, throughout the whole of the project, the following dimensions must be 
considered:

* Size of input
* Size of output
* Relational distance between input and output

The first two have a simple difficulty classification - difficulty increases 
with the output size and inversely with the input size. Though this relation 
is not linear, it should serve well as a means of scaling the difficulty of 
the AI's task. Relation is slightly more complicated, as it has many aspects 
to consider. Notes after the first within a single bar will typically have a 
strong correlation with the note(s) immediately prior, while the first note in 
a given bar is often more likely to have a stronger correlation with the first 
note of the previous bar. This only increases in complexity when taking into 
account different phases, sections, and voices, and will heavily vary across 
different genres of music. Therefore testing the ability of the AI to cope 
with distant relations should take place later during the project, using a set 
of hand-picked tests based on the genre being tested. 

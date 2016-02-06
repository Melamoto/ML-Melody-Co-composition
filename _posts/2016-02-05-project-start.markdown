---
layout: post
title:  "Project: Start"
date:   2016-02-05 21:00:00 +0000
categories: progress update milestone
---
### The project

This blog is dedicated to the study and creation of an application that uses 
machine learning to compose music cooperatively with a human composer. Over the
course of this project I will be experimenting with various existing methods 
for AI melodic composition as applied to this problem, and potentially creating
novel variations or extensions of these methods.

As of this post, no tangible progress has been made toward this goal; all
progress made will be presented in future blog posts, made regularly throughout
this project. The development tactic in this research project is to rapidly
create prototype solutions, collect results, and use those results to guide 
development of the next solution. The goal of this is to map out the 
hindrances to this project as soon as possible, allowing the majority of 
development time to be spent solving these issues instead of exploring 
dead-ends.

In order for the project to be successful, a set of tasks must be completed. 
These tasks comprise the whole of the project, and may not have a single best 
solution. It is not expected nor entirely possible that they be completed 
sequentially - instead, each major milestone of the project may be defined by 
the satisfaction of a set of objectives that the AI strives to achieve. 
Defining these objectives is itself another necessary task to be completed, 
albeit separate from the others in that it does not directly develop the 
final product.

### Tasks

The first major task is appropriate representation of musical data. Though 
there exist many data formats in which music can be stored, such as MIDI or 
MusicXML, these formats do not lend themselves well to machine learning. They 
have a high dimensionality that increases the complexity of analysis hugely, 
and do not necessarily give the best representation of the features that are 
useful in composition; for example, using absolute instead of relative pitch 
encoding. Different data representations may affect the outcome of an ML 
method, so the ideal representation should be determined empirically. 

The second major task is the discovery of the optimal algorithm for melodic 
co-composition. This is expected to be the most difficult task, and is 
essentially the goal of this project. There have been many methods previously 
employed in melodic composition, each with their own advantages, 
disadvantages, and restrictions. The success of a given method can be 
determined empirically by testing performance against the AI's objectives. 
Importantly, each method comes with requirements that may be difficult to 
provide and will heavily affect the method's performance, such as a set of 
training data, a fitness grading function, or a set of constraints. 

The third and final task is the creation of the application that directly 
completes the objectives of this project. Included as part of this task are 
the selection of the programming language, libraries, and tools used in the 
application. This is important at all stages of the project, as these decisions 
will affect the availability of ML methods, the efficiency of the AI, and the 
speed of development. Of particular importance early on is the ability to read 
and encode MIDI files to be used as input/training data. 

### The first step

In accordance with the goals previously stated, the first act of the project 
is to produce a prototype that is able to satisfy one or more of the 
AI's objectives. This will require progress to be made in all of the above 
tasks, and will also require concrete target objectives. I will be defining 
these objectives and attempting to create this prototype over the course of 
the next week, with regular progress updates throughout.


---
layout: page
title: "Software"
weight: 4
description: "Solvers for nonsmooth optimization problems and other utilities I wrote in C, Julia, MATLAB."
permalink: /software/
---

# Software

Software I've been working on (also check out my [Github profile](https://github.com/{{ site.author.github }})):

[ProximalAlgorithms.jl](https://github.com/kul-forbes/ProximalAlgorithms.jl). Efficient, generic Julia implementations of first-order optimization algorithms for nonsmooth problems, based on operator splittings: forward-backward splitting (proximal gradient method), Douglas-Rachford splitting (ADMM), Newton-type methods, primal-dual splitting algorithms. Based on:

[ProximalOperators.jl](https://github.com/kul-forbes/ProximalOperators.jl). Julia package to compute the proximal operator of several functions commonly used in nonsmooth optimization problems. Useful as building block to implement large-scale optimization algorithms such as ADMM.

[ForBES](http://kul-forbes.github.io/ForBES/). MATLAB solver for nonsmooth optimization, contains a library of
mathematical functions to formulate problems arising in control, machine
learning, image and signal processing.

[libLBFGS](http://github.com/lostella/libLBFGS/). C library providing the structures and routines to implement the
limited-memory BFGS algorithm (L-BFGS) for large-scale smooth unconstrained
optimization. Contains a Mex interface to MATLAB.

[libForBES](http://kul-forbes.github.io/libForBES/). C++ framework for modeling and solving large-scale nonsmooth
optimization problems, will allow to interface many high-level languages
(including R, Python, Julia) to a unique solver capable of addressing nonsmooth
optimization problems from several application fields.

### Just for fun

[Matto](http://github.com/lostella/matto/). A simple chess player implemented in C. I started this when I was 17
and learning the C programming language, so there's a lot of room for
improvement. Yet it plays!

[podds](http://github.com/lostella/podds/). A multi-threaded Texas hold 'em poker odds evaluation tool, written in C, command line only.

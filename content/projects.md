+++
title = "Projects"
menu = "main"
+++

Things I've been working on (also check out my [Github profile](https://github.com/lostella)):

* [ProtoGrad](https://github.com/lostella/ProtoGrad.jl). An experimental Julia package for gradient-based optimization of machine learning models.
Essentially, a highly opinionated collection of design ideas of mine, on how deep learning frameworks should work.

* [GluonTS](https://github.com/awslabs/gluon-ts). Python toolkit for probabilistic time series modeling, with a focus on deep learning architectures, built around [PyTorch](https://pytorch.org/).

* [ProximalAlgorithms.jl](https://github.com/kul-forbes/ProximalAlgorithms.jl). Generic Julia implementations of first-order optimization algorithms for nonsmooth problems, based on operator splittings: forward-backward (proximal gradient method), Douglas-Rachford (ADMM), primal-dual, and Davis-Yin splitting algorithms. Also contains Newton-type extensions. Based on:

* [ProximalOperators.jl](https://github.com/kul-forbes/ProximalOperators.jl). Julia package to compute the proximal operator of several functions commonly used in nonsmooth optimization problems. Useful as building block to implement large-scale optimization algorithms such as ADMM.

* [libLBFGS](http://github.com/lostella/libLBFGS/). C library providing the structures and routines to implement the
limited-memory BFGS algorithm (L-BFGS) for large-scale smooth unconstrained
optimization. Contains a Mex interface to MATLAB.

* [Matto](http://github.com/lostella/matto/). Simple chess player implemented in C. I started this when I was 17
and learning the C programming language, so there's a lot of room for
improvement. Yet it plays!

* [podds](http://github.com/lostella/podds/). Multi-threaded Texas hold 'em poker odds evaluation tool, written in C, command line only.

---
layout: post
title: "Iterative methods done right (life's too short to write for-loops)"
description: "Notes on iterative methods implementation using Julia iterables."
image: /img/dodici.png
tags: [ iterative methods, julia, iterables ]
date: 2018-07-25
updated: 2018-07-31
mathjax: true
---

Iterative methods are a class of numerical algorithms that produce a sequence of
(hopefully) better and better approximations to a solution of a problem,
starting from an initial guess. Function minimization, linear and nonlinear
systems of equations, are very often solved with iterative methods (especially
when the problem is too large for direct methods to kick in).

On paper, iterative methods are commonly
described as loops that somehow generate a sequence of approximations to the
problem solution: in fact, that's the immediate way of translating them into
running pieces of code using the programming language of choice.
Include a bit of additional logic (some stopping condition to halt the
iterations, a few lines to display the algorithm's status or log it to a file)
and one has a pretty decent utility to run experiments.

However, that's not necessarily *the best* way of doing the job, especially if
you need to code this type of loops over and over again:
[off-by-one-errors](https://en.wikipedia.org/wiki/Off-by-one_error) are
around the corner, and adding options and features one on top of the other
quickly results in [spaghetti code](https://en.wikipedia.org/wiki/Spaghetti_code)
(which [may not necessarily be a bad thing](https://www.economist.com/science-and-technology/2016/03/23/of-more-than-academic-interest)).

Instead, common patterns that show up when implementing iterative methods are
much better exploited using *iterables*.
I'll illustrate this by examples in [Julia](https://julialang.org/), using the
[conjugate gradient method](https://www.cs.cmu.edu/~quake-papers/painless-conjugate-gradient.pdf)
for positive (semi)definite linear systems as guinea pig.

*Note:* the examples that follow run on Julia 0.7 (as well as 1.0,
but that's not out yet).
It goes without saying that similar things one can do in
[Python](https://docs.python.org/3/tutorial/classes.html#iterators),
[Java](https://docs.oracle.com/javase/10/docs/api/java/util/Iterator.html),
[C++](https://www.cs.helsinki.fi/u/tpkarkka/alglib/k06/lectures/iterators.html),
or whatever language is preferred: in fact, I would highly encourage you to do so
in case you have months (or years) ahead of experimenting with iterative methods.

## Iterables in Julia

Iterables are objects one can iterate on, like lists or other types of collections.
Unlike collections however, iterables do not hold all elements in memory: instead,
they only need to be able to generate them in sequence, one after the other.
They're like *lazy* collections.
In order to make
[custom iterable types in Julia](https://docs.julialang.org/en/latest/manual/interfaces/#man-interface-iteration-1),
it is sufficient to identify what the *state* of the iteration is,
and define the `iterate` function returning the next element in the sequence
and updated state.

For instance, suppose we want to compute the following generalized Fibonacci sequence:

$$
\begin{align}
F_{0} &= s_{0}, \\
F_{1} &= s_{1}, \\
F_{n} &= F_{n-1} + F_{n-2},\quad\forall\ n > 1.
\end{align}
$$

The sequence is uniquely determined by $$s_0$$ and $$s_1$$
(with $$s_0=0$$, $$s_1=1$$ yielding the
[standard Fibonacci sequence](https://oeis.org/A000045)).
So our iterable is

{% highlight julia %}
struct FibonacciIterable{I}
  s0::I
  s1::I
end
{% endhighlight %}

In order to unroll the sequence and compute each element, one only needs to keep
track of the pair $$(F_{n-1}, F_{n})$$ of the two most recent elements: that
will be the state of our iteration. Then we need to define *two*
methods for the `iterate` function:
* `iterate(iter::FibonacciIterable)` returning the pair `(F0, state0)` containing
the *first* element in the sequence and initial state respectively;
* `iterate(iter::FibonacciIterable, state)` returning the pair `(F, newstate)`
of the *next* element `F` in the sequence (given `state`) and the updated state
`newstate`.

As soon as the sequence is over, `iterate` should return
`nothing` (Julia's "none" value). This is never the case for our Fibonacci
sequences, since they're infinite.
Note that `FibonacciIterable` objects are immutable: we would like them not
to change as we iterate, since they *identify* the sequence which is being produced.
Instead, all mutations should occur in state updates.

The following definitions give exactly the above described generalized Fibonacci
sequence:

{% highlight julia %}
import Base: iterate
iterate(iter::FibonacciIterable) = iter.s0, (iter.s0, iter.s1)
iterate(iter::FibonacciIterable, state) = state[2], (state[2], sum(state))
{% endhighlight %}

We can now loop any `FibonacciIterable` object:

{% highlight julia %}
julia> for F in FibonacciIterable(BigInt(0), BigInt(1))
           println(F)
           if F > 50 break end
       end
0
1
1
2
3
5
8
13
21
34
55
{% endhighlight%}

## The conjugate gradient method

The conjugate gradient (CG) method solves linear systems

$$
Ax = b
$$

where $$A\in\mathbb{R}^{n\times n}$$ is a positive semidefinite, symmetric matrix.
It is particularly useful when $$n$$ is very large and $$A$$ is sparse,
in which case direct methods (Cholesky factorization) are computationally
prohibitive. Instead, CG works by only applying matrix-vector products with
$$A$$. Given an initial guess $$x_0$$, the method produces a sequence $$x_k$$
of solution approximations according to the following recurrence:

1. Initialize $$ r_0 = p_0 = Ax_0 - b $$.
2. For any $$k > 0$$ do

$$
\begin{align}
\alpha_k &= \frac{\|r_k\|^2}{\langle p_k, Ap_k \rangle}, \\
x_{k+1} &= x_{k} + \alpha_{k} p_{k}, \\
r_{k+1} &= r_{k} + \alpha_{k} A p_{k}, \\
p_{k+1} &= r_{k+1} + \frac{\|r_{k+1}\|^2}{\|r_{k}\|^2}p_{k}. \\
\end{align}
$$

See [here](https://www.cs.cmu.edu/~quake-papers/painless-conjugate-gradient.pdf)
for a detailed derivation of the method.

Let's now translate CG into a Julia iterable type.
The iteration is completely determined by matrix $$A$$, vector $$b$$, and
the initial guess $$x_0$$, so those will compose our iterable objects:

{% highlight julia %}
{% include code/iterative-methods-done-right/cg/cg_iterable.jl %}
{% endhighlight %}

In the `cgiterable` constructor we allow for `x0` to be `nothing`: in this case
we will assume the initial point to be the zero vector, and save ourselves one
matrix-vector product.
The *state* of the iteration is composed of vectors $$x_k$$, $$r_k$$, and $$p_k$$.
In addition to that, we will make room for additional stuff, so as to reuse all
possible memory and avoid allocations: vector $$A p_k$$ and scalars $$\|r_k\|^2$$
and $$\|r_{k+1}\|^2$$.
Overall, the state for CG is a bit more complex than in the Fibonacci example,
and keeping it in a `Tuple` would be impractical. So let's give things a name
by defining a custom type for the state:

{% highlight julia %}
{% include code/iterative-methods-done-right/cg/cg_state.jl %}
{% endhighlight %}

Note that `CGState` is defined as `mutable`: this is because we will overwrite
the iteration state rather than allocate new objects, again for efficiency reasons.

The actual computation is carried out by the `iterate` function:

{% highlight julia %}
{% include code/iterative-methods-done-right/cg/cg_iterate.jl %}
{% endhighlight %}

Rather than the sequence of $$x_k$$, we yield the sequence of states of the
algorithm, since that contains all information that may be needed when
experimenting (including $$x_k$$ itself).

## Wrapping iterables

Given the simplicity of the method, it is easy to check that the iterable type
we just defined is a correct CG implementation. However, there are some
apparent shortcomings:
1. The produced sequence is infinite, and iterating over it will result in an
infinite loop.
2. As $$\|r_k\|^2$$ (that is, `state.rsprev`) approaces zero, numerical issues
appear due to divisions.
3. No useful information is displayed onto the screen.

For the first problem, we can simply impose a maximum number of iterations
by doing

{% highlight julia %}
k = 1
for state in cgiterable(A, b)
  # do something
  if k >= maxit break end
  k += 1
end
{% endhighlight %}

This is not best practice: if `k` is touched elsewhere in the loop,
then it can be mishandled, change value, and the counting logic be broken.
And in any case: counting iterations and stopping at a prescribed limit
is something one *always* wants to do, so we better have a correct, robust,
reusable way of doing it.

A cleaner solution is

{% highlight julia %}
for (k, state) in Base.Iterators.enumerate(cgiterable(A, b))
  # do something
  if k >= maxit break end
end
{% endhighlight %}

or, even better

{% highlight julia %}
for state in Base.Iterators.take(cgiterable(A, b), maxit)
  # do something
end
{% endhighlight %}

Here we are using some of Julia's [built-in iteration utilities](https://docs.julialang.org/en/latest/base/iterators/):
* `enumerate` takes an iterable producing a sequence of `s`, and returns
an iterable producing pairs `(k, s)`, where `k` is the (1-based) index of `s`
in the original sequence;
* `take` takes an additional integer `n` and returns a truncated iterable that
only yields the first `n` elements in the original sequence.

These are iterable *wrappers*: given an iterable (i.e. a sequence)
they wrap a new one around it that somehow extends its behaviour.
What's most important here is that we get to add features on top of our original
iteration *without ever touching its code*.

In this spirit, let us now define more of these iterable wrappers that are
useful when working with iterative methods, and nicely address problems 2 and 3
above (among other things) without getting in the way of our CG implementation.

## Halting

Aside from imposing a maximum number of iterations, one usually wants to stop
the computation as soon as some condition is met. Here the `halt` wrapper takes an
iterable `iter` and a boolean function `fun`: a new iterable is returned that
applies `fun` to each element of `iter` until `true` is returned, at which point
the iteration stops.

{% highlight julia %}
{% include code/iterative-methods-done-right/tools/halt.jl %}
{% endhighlight %}

## Side effects

This is a simple but powerful one: for a given sequence, apply some function to
each of its elements, and yield the same original sequence.
I'm calling this wrapper `tee`, like the
[standard Unix T-pipe command](http://man7.org/linux/man-pages/man1/tee.1.html),
because of the apparent analogy.

{% highlight julia %}
{% include code/iterative-methods-done-right/tools/tee.jl %}
{% endhighlight %}

This can be used to display some summary of the algorithm's state
(number of iterations, most relevant quantities, maybe a progress bar).
Or, in the case of distributed algorithms, one can use this to encapsulate a
synchronization mechanism through which agents communicate and exchange information.
Note that this is conceptually different from
[callbacks](https://stackoverflow.com/questions/824234/what-is-a-callback-function/7549753#7549753).

## Sampling

Not always you want to do something with *all* elements in a sequence.
Sometimes you want to consider, say, every tenth element and do something about it.
For instance, displaying information on the screen at every iteration may be
too much overhead if each iteration takes 20 microseconds, or if there is
five thousands of them.
Or maybe you need to compute some relatively expensive stopping criterion,
and you only want to do that every once in a while.

The `sample` wrapper does exactly this. It is pretty similar [to the `takenth` wrapper
from IterTools.jl](https://github.com/JuliaCollections/IterTools.jl/blob/v1.0.0/src/IterTools.jl#L632),
with a difference: with `sample`, the last element in the original sequence
is always included in the filtered sequence. This is very important, since one
is precisely interested in the final state of an iterative algorithm&mdash;the
one that triggered the prescribed stopping criterion.

{% highlight julia %}
{% include code/iterative-methods-done-right/tools/sample.jl %}
{% endhighlight %}

## Timing

Just like `enumerate` counts the elements as a sequence unfolds,
here `stopwatch` measures time elapsed from the beginning
([in nanoseconds](https://docs.julialang.org/en/latest/base/base/#Base.time_ns)).

{% highlight julia %}
{% include code/iterative-methods-done-right/tools/stopwatch.jl %}
{% endhighlight %}

Measuring time in the context of numerical algorithms needs no justification, I believe.

## Putting it all together

There's another piece of code that we can factor out and put in our toolbox:
the `for` loop. The following function takes whatever iterable, loops
over it until it's finished (so it better be finite), and returns the last
element:

{% highlight julia %}
{% include code/iterative-methods-done-right/tools/loop.jl %}
{% endhighlight %}

We now have all pieces to assemble our CG solver routine.
In the following snippet, the `cg` function instantiates a `CGIterable` object
for the given problem, buries it under the wrappers we described above,
then loops the resulting iterable to get the last state.
For simplicity, the composition of iterables is fixed, but one could think of
parsing here all sorts of options the user may provide (e.g. verbose/silent,
measure time/do not measure time, using multiple termination criteria...)
and cook up the iterable accordingly.

{% highlight julia %}
{% include code/iterative-methods-done-right/cg/cg_doneright.jl %}
{% endhighlight %}

A quick test on a random, small, dense linear system shows the routine in action:

{% highlight julia %}
julia> using Random

julia> srand(12345);

julia> n = 100; L = randn(n, n); A = L*L'; b = randn(n);

julia> x, it = cg(A, b, tol=1e-8, period=30);
   30 | 2.210e-04 | 4.555e+00
   60 | 4.029e-02 | 1.642e+00
   90 | 6.232e-02 | 1.703e+00
  120 | 8.149e-02 | 4.277e-01
  150 | 1.162e-01 | 9.656e-05
  158 | 1.480e-01 | 5.655e-09

julia> norm(A*x - b)
5.65469997682613e-9
{% endhighlight %}

## Conclusions

Implementing iterative methods as iterables has some advantages with respect
to writing explicit, monolithic for-loops: above all, "core" computations are
well isolated from all additional logics and can be modified,
optimized, checked for correctness (and *unit tested*) much more easily.
Additional functionalities (stopping criteria, I/O, ...) can be wrapped around
the core method, as well as tested, and stored for future usage. Ultimately,
writing a solver amounts to designing its interface, options, and coding the
logic that builds the right iterable.

In this post I've outlined a rather minimal set of iterables, and only explored
the simple example of CG. However, using this design one should be able
to implement and glue together many other kinds of pieces:
* Computing preconditioners (e.g. quasi-Newton or L-BFGS).
* Step-size selection rules (including line-searches).
* Nesterov acceleration (fast gradient methods).
* Restart (e.g. for GMRES or fast gradient methods).

Intuitively, all of these could be implemented using the `tee` wrapper defined
above (when, like in the case of `CGIterable`, the "elements" that `TeeIterable`
handles are the *mutable* states of our iteration) or could be implemented as
separate building blocks. In any case, that's material for future thinking.

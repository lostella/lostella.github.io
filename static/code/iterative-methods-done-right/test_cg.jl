'''
include("cg/cg_donewrong.jl")
include("cg/cg_iterable.jl")
include("cg/cg_state.jl")
include("cg/cg_iterate.jl")
include("tools/halt.jl")
include("tools/tee.jl")
include("tools/stopwatch.jl")
include("tools/sample.jl")
include("tools/loop.jl")
include("cg/cg_doneright.jl")
'''

using Random
using LinearAlgebra
using Test
using BenchmarkTools

Random.seed!(123456)

n = 100

Q = randn(n, n)
A = Q'*Q
b = randn(n)
x0 = randn(n)

@time x_wrong, it_wrong = cg_donewrong!(A, b, x=copy(x0))

println(it_wrong)
println(norm(A*x_wrong - b))

@time x_right, it_right = cg(A, b, x0=x0)

println(it_right)
println(norm(A*x_right - b))

# @test all(x_right .== x_wrong)

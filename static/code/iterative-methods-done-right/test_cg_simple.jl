julia> include("cg/cg_iterable.jl")

julia> include("cg/cg_state.jl")

julia> include("cg/cg_iterate.jl")

julia> include("tools/halt.jl")

julia> include("tools/tee.jl")

julia> include("tools/stopwatch.jl")

julia> include("tools/sample.jl")

julia> include("tools/loop.jl")

julia> include("cg/cg_doneright.jl")

julia> using Random

julia> Random.seed!(12345);

julia> n = 100; L = randn(n, n); A = L*L'; b = randn(n);

julia> x, it = cg(A, b, tol=1e-8, period=30);

julia> norm(A*x - b)

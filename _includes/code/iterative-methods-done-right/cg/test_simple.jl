julia> include("cg_iterable.jl")

julia> include("cg_state.jl")

julia> include("cg_iterate.jl")

julia> include("halt.jl")

julia> include("tee.jl")

julia> include("stopwatch.jl")

julia> include("sample.jl")

julia> include("loop.jl")

julia> include("cg_doneright.jl")

julia> using Random

julia> srand(12345);

julia> n = 100; L = randn(n, n); A = L*L'; b = randn(n);

julia> x, it = cg(A, b, tol=1e-8, period=30);

julia> norm(A*x - b)

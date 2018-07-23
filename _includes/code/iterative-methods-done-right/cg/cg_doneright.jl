using Base.Iterators # so we can use `take` and `enumerate`
using Printf # so we can use the `@printf` macro

stop(state) = sqrt(state.rs) <= tol

disp(state) = @printf "%5d | %.3e | %.3e\n" state[2][1] state[1]/1e9 sqrt(state[2][2].rs)

function cg(A::TA, b::Tb; x::Tx=nothing, tol=1e-6, maxit=max(1000,size(A,2)),
    period=div(size(A,2),10)) where {TA, Tb, Tx}

    iter = CGIterable{TA, Tb, Tx}(A, b, x)
    iter = halt(iter, stop)
    iter = take(iter, maxit)
    iter = enumerate(iter)
    iter = sample(iter, period)
    iter = stopwatch(iter)
    iter = tee(iter, disp)

    (_, (it, state)) = loop(iter)

    return state.x, it
end

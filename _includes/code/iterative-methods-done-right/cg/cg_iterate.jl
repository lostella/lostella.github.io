using LinearAlgebra
import Base: iterate

function iterate(iter::CGIterable{TA, Tb, Tx}) where
    {R, TA, Tb <: AbstractVector{R}, Tx}
    if iter.x0 === nothing
        x = zero(iter.b)
        r = copy(iter.b)
    else
        x = copy(iter.x0)
        r = iter.A*x
        r .*= -one(R)
        r .+= iter.b
    end
    rs = dot(r, r)
    p = copy(r)
    Ap = similar(r)
    state = CGState{R, Tb}(x, r, rs, zero(rs), p, Ap)
    return state, state
end

function iterate(iter::CGIterable{TA, Tb, Tx}, state::CGState{R, Tb}) where
    {R, TA, Tb <: AbstractVector{R}, Tx}
    mul!(state.Ap, iter.A, state.p)
    alpha = state.rs / dot(state.p, state.Ap)
    state.x .+= alpha .* state.p
    state.r .-= alpha .* state.Ap
    state.rsprev = state.rs
    state.rs = dot(state.r, state.r)
    state.p .= state.r .+ (state.rs / state.rsprev) .* state.p
    return state, state
end

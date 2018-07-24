struct HaltingIterable{I, F}
    iter::I
    fun::F
end

function iterate(iter::HaltingIterable)
    next = iterate(iter.iter)
    return dispatch(iter, next)
end

function iterate(iter::HaltingIterable, (instruction, state))
    if instruction == :halt return nothing end
    next = iterate(iter.iter, state)
    return dispatch(iter, next)
end

function dispatch(iter::HaltingIterable, next)
    if next === nothing return nothing end
    return next[1], (iter.fun(next[1]) ? :halt : :continue, next[2])
end

halt(iter::I, fun::F) where {I, F} = HaltingIterable{I, F}(iter, fun)

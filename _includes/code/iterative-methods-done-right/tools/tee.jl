struct TeeIterable{I, F}
    iter::I
    fun::F
end

function iterate(iter::TeeIterable, args...)
    next = iterate(iter.iter, args...)
    if next !== nothing iter.fun(next[1]) end
    return next
end

tee(iter::I, fun::F) where {I, F} = TeeIterable{I, F}(iter, fun)

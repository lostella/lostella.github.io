struct StopwatchIterable{I}
    iter::I
end

function iterate(iter::StopwatchIterable)
    t0 = time_ns()
    next = iterate(iter.iter)
    return dispatch(iter, t0, next)
end

function iterate(iter::StopwatchIterable, (t0, state))
    next = iterate(iter.iter, state)
    return dispatch(iter, t0, next)
end

function dispatch(iter::StopwatchIterable, t0, next)
    if next === nothing return nothing end
    return (time_ns()-t0, next[1]), (t0, next[2])
end

stopwatch(iter::I) where I = StopwatchIterable{I}(iter)

struct SamplingIterable{I}
    iter::I
    period::UInt
end

function iterate(iter::SamplingIterable, state=iter.iter)
    current = iterate(state)
    if current === nothing return nothing end
    for i = 1:iter.period-1
        next = iterate(state, current[2])
        if next === nothing return current[1], rest(state, current[2]) end
        current = next
    end
    return current[1], rest(state, current[2])
end

sample(iter::I, period) where I = SamplingIterable{I}(iter, period)

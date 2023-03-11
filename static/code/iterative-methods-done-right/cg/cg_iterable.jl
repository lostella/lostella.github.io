struct CGIterable{TA, Tb, Tx}
    A::TA
    b::Tb
    x0::Tx
end

cgiterable(A::TA, b::Tb; x0::Tx=nothing) where {TA, Tb, Tx} = CGIterable{TA, Tb, Tx}(A, b, x0)

struct PGIterable{Tf, Tg, Tx}
    f::Tf
    g::Tg
    x0::Tx
end

mutable struct PGState{R, Tx}
    x::Tx
end

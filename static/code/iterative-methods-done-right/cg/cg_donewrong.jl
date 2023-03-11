function cg_donewrong!(A, b; x=nothing, tol=1e-6, maxit=1000)
    if x isa Nothing
        x = zero(b)
        r = copy(b)
    else
        r = A*x
        r .*= -1
        r .+= b
    end
    p = copy(r)
    Ap = similar(r)
    rs = dot(r, r)
    it = 1
    while it <= maxit && sqrt(rs) > tol
        mul!(Ap, A, p)
        alpha = rs / dot(p, Ap)
        x .+= alpha .* p
        r .-= alpha .* Ap
        rsold = rs
        rs = dot(r, r)
        p .= r .+ (rs / rsold) .* p
        it += 1
    end
    return x, it
end

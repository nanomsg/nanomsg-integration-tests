from nanomsg import Socket, REP


def factorize_naive(n):
    """ A naive factorization method. Take integer 'n', return list of
        factors.
    """
    if n < 2:
        return []
    factors = []
    p = 2

    while True:
        if n == 1:
            return factors

        r = n % p
        if r == 0:
            factors.append(p)
            n = n / p
        elif p * p >= n:
            factors.append(n)
            return factors
        elif p > 2:
            # Advance in steps of 2 over odd numbers
            p += 2
        else:
            # If p == 2, get to 3
            p += 1
    assert False, "unreachable"

    return factors


def main():
    sock = Socket(REP)
    sock.bind('tcp://0.0.0.0:10001')
    while True:
        num = int(sock.recv())
        res = factorize_naive(num)
        sock.send(','.join(map(str, res)).encode('ascii'))


if __name__ == '__main__':
    main()


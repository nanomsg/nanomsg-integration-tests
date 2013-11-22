import argparse

from nanomsg import Socket, REP, PULL, PUSH, SOL_SOCKET, SOCKET_NAME


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
    ap = argparse.ArgumentParser()
    gr = ap.add_mutually_exclusive_group()
    gr.add_argument('--rep', metavar="URL",
        help="The topology url of replier socket")
    gr.add_argument('--pullpush', metavar="URL", nargs=2,
        help="The topology urls of pull and push sockets for request processing")
    options = ap.parse_args()

    if options.rep:
        sock = Socket(REP)
        sock.configure(options.rep)
        sock.set_string_option(SOL_SOCKET, SOCKET_NAME, "rep")
        read = write = sock
    else:
        read = Socket(PULL)
        read.set_string_option(SOL_SOCKET, SOCKET_NAME, "pull")
        write = Socket(PUSH)
        write.set_string_option(SOL_SOCKET, SOCKET_NAME, "push")

        read.configure(options.pullpush[0])
        write.configure(options.pullpush[1])


    while True:
        num = int(read.recv())
        res = factorize_naive(num)
        formula = str(num) + '=' + '*'.join(map(str, res))
        write.send(formula.encode('ascii'))


if __name__ == '__main__':
    main()


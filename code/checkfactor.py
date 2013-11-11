from __future__ import print_function

import time
import argparse
import random
from functools import reduce

from nanomsg import Socket, REQ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-n', '--requests', metavar="NUM",
        help="Number of requests to issue (default %(default)d)",
        default=10000, type=int)
    ap.add_argument('-m', '--max-value', metavar="NUM",
        help="Maximum number that's sent for factorizing (default %(default)d)",
        default=10**12, type=int)
    ap.add_argument('--min-value', metavar="NUM",
        help="Maximum number that's sent for factorizing (default %(default)d)",
        default=10**11, type=int)
    ap.add_argument('--connect', metavar="ADDR", required=True,
        help="Nanomsg address to connect to",
        default=[], action='append')
    options = ap.parse_args()

    sock = Socket(REQ)
    for c in options.connect:
        sock.connect(c)

    start_time = time.time()
    for i in range(options.requests):
        val = random.randint(options.min_value, options.max_value)
        sock.send(str(val).encode('ascii'))
        factors = map(int, sock.recv().decode('ascii').split(','))
        checkval = reduce(int.__mul__, factors)
        assert val == checkval

    sec = time.time() - start_time
    print("Done", options.requests, "requests in", sec, "seconds")


if __name__ == '__main__':
    main()

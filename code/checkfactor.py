from __future__ import print_function

import os
import time
import argparse
import random
from functools import reduce

from nanomsg import Socket, REQ


os.environ['NN_APPLICATION_NAME'] = 'checkfactor'


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
    ap.add_argument('--topology', metavar="ADDR",
        help="Nanoconfig topology to connect to",
        default=None)
    options = ap.parse_args()

    sock = Socket(REQ)
    sock.configure(options.topology)

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

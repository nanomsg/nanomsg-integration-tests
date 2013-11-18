from __future__ import print_function

import struct
import os
import time
import argparse
import random
from functools import reduce

from nanomsg import Socket, REQ, AF_SP_RAW, SOCKET_NAME


os.environ['NN_APPLICATION_NAME'] = 'checkfactor'
REQUEST_MASK = (1 << 31)-1


def requests(options):
    start_rid = random.randrange(1 << 31)
    for i in range(options.requests):
        rid = (start_rid + i) & REQUEST_MASK
        val = random.randint(options.min_value, options.max_value)
        yield rid, val


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-n', '--requests', metavar="NUM",
        help="Number of requests to issue (default %(default)d)",
        default=10000, type=int)
    ap.add_argument('-c', '--concurrent', metavar="NUM",
        help="Number of requests sent simultaneously (default %(default)d)",
        default=1000, type=int)
    ap.add_argument('-m', '--max-value', metavar="NUM",
        help="Maximum number that's sent for factorizing (default %(default)d)",
        default=10**12, type=int)
    ap.add_argument('--min-value', metavar="NUM",
        help="Maximum number that's sent for factorizing (default %(default)d)",
        default=10**11, type=int)
    options = ap.parse_args()

    sock = Socket(REQ, domain=AF_SP_RAW)
    sock.setsockopt(SOCKET_NAME, "factor")
    sock.configure(os.environ["TOPOLOGY_URL"])

    start_time = time.time()
    reqiter = requests(options)
    req = {}
    for i in range(options.concurrent):
        rid, val = next(reqiter)
        sock.send(b'\x00\x00\x00\x00' + struct.pack('>L', rid | 0x80000000)
            + str(val).encode('ascii'))
        req[rid] = val
    errors = 0
    sp  = 0
    n = 0
    while req:
        data = sock.recv()
        rid = struct.unpack_from('>L', data)[0] & ~0x80000000
        factors = map(int, data[4:].decode('ascii').split(','))
        checkval = reduce(int.__mul__, factors)
        if rid not in req:
            sp += 1
        elif req.pop(rid) != checkval:
            errors += 1
        else:
            n += 1

        try:
            rid, val = next(reqiter)
        except StopIteration:
            continue
        else:
            sock.send(b'\x00\x00\x00\x00' + struct.pack('>L', rid | 0x80000000)
                + str(val).encode('ascii'))
            req[rid] = val

    sec = time.time() - start_time
    print("Done", options.requests, "requests in", sec,
          "seconds, errors:", errors, ", spurious messages:", sp)


if __name__ == '__main__':
    main()

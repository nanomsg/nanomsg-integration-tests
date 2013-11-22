from __future__ import print_function

import argparse
import random
from functools import reduce

from nanomsg import Socket, PULL, SOL_SOCKET, SOCKET_NAME


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topology', metavar="URL", required=True,
        help="Url for topology to join to")
    options = ap.parse_args()

    sock = Socket(PULL)
    sock.set_string_option(SOL_SOCKET, SOCKET_NAME, "push")
    sock.configure(options.topology)

    while True:
        data = sock.recv()
        num, factors = data.decode('ascii').split('=', 1)
        factors = map(int, factors.split('*'))
        checkval = reduce(int.__mul__, factors)
        assert int(num) == checkval


if __name__ == '__main__':
    main()

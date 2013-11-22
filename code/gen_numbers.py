from __future__ import print_function

import time
import argparse
import random

from nanomsg import Socket, PUSH, SOL_SOCKET, SOCKET_NAME


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-n', '--rate-limit', metavar="NUM",
        help="Number of requests to issue per second (default %(default)d)",
        default=100, type=float)
    ap.add_argument('-m', '--max-value', metavar="NUM",
        help="Maximum number that's sent for factorizing (default %(default)d)",
        default=10**12, type=int)
    ap.add_argument('--min-value', metavar="NUM",
        help="Maximum number that's sent for factorizing (default %(default)d)",
        default=10**11, type=int)
    ap.add_argument('--topology', metavar="URL", required=True,
        help="Url for topology to join to")
    options = ap.parse_args()

    delay = 1.0 / options.rate_limit
    sock = Socket(PUSH)
    sock.set_string_option(SOL_SOCKET, SOCKET_NAME, "push")
    sock.configure(options.topology)

    while True:
        tm = time.time()
        num = random.randint(options.min_value, options.max_value)
        sock.send(str(num))
        to_sleep = tm + delay - time.time()
        if to_sleep > 0:
            time.sleep(to_sleep)


if __name__ == '__main__':
    main()

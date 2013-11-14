===========
Factor Test
===========

This test runs workers that factorize an integer, and a simple load generator
on the master.

Synopsis::

    make clean test NWORKERS=3

You also need some bridge interface with DHCP available to interconnect
vagrant nodes. The ``br0`` is assumed. You may override it::

    make test NWORKERS=10 BRIDGE=lxcbr0

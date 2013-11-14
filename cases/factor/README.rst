===========
Factor Test
===========

This test runs workers that factorize an integer, and a simple load generator
on the master.

Synopsis::

    make test NWORKERS=3 NREQUESTS=10000

You also need some bridge interface with DHCP available to interconnect
vagrant nodes. The ``br0`` is assumed. You may override it::

    make test BRIDGE=lxcbr0

Cleaning After Tests
====================

After test run, machines are still running in case you will run another test or
want to inspect machine state. So you can shutdown them with::

    make clean

If you change test parameters (except NREQUESTS) its recommented to rebuild
everything with::

    make clean test NWORKERS=10


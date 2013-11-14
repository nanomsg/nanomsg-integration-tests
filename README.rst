=========================
Nanomsg Integration Tests
=========================


Running Tests
=============


Prepare Projects
----------------

First make sure that submodules are up to date::

    git submodule update --init --recursive

You may also checkout specific versions of each of the project in the
``projects`` directory.


Base Vagrant Box
----------------

Tests are run with vagrant. First we need to build vagrant box for the virtual
machines. Add base Ubuntu Precise 64bit as base vagrant box, here are quick
links:

* ``virtualbox`` provider (default): http://files.vagrantup.com/precise64.box
* ``lxc`` provider: http://bit.ly/vagrant-lxc-precise64-2013-10-23

Other image and providers can be used too. Feel free to report any bugs and
add more links here. In particular, running tests on cloud hostings is very
encouraged. Note you should export ``VAGRANT_DEFAULT_PROVIDER`` to change
vagrant provider for the tests.


Add base box as ``nntest_base``::

    vagrant box add nntest_base <URL>
    make -C projects box

If everything is OK it builds ``projects/nntest.box``. You should add it
as vagrant box ``nntest``:

    vagrant box add nntest projects/nntest.box

Now you may provision test containers.


Real Tests
----------

All test cases are in ``cases`` directory. You may run any like this::

    cd cases/factor
    cat README.rst
    make test

If test runs successfully you will get some results in ``reports`` directory.


Host Dependencies
=================

Here are the list of base dependencies you should have installed on the host
to run the tests:

* vagrant
* make
* rrdtool
* rsync

You also need whatever your vagrant provider needs (e.g. virtualbox itself
by default).

Everything else including nanomsg, and other test objects are installed
automatically inside the virtual machines

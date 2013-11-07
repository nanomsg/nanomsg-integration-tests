=========================
Nanomsg Integration Tests
=========================


Running Tests
=============

Base Vagrant Box
----------------

Tests are run with vagrant. First we need to build vagrant box for the virtual
machines. Add base Ubuntu Precise 64bit as base vagrant box, here are quick
links:

* ``virtualbox`` provider (default): http://files.vagrantup.com/precise64.box
* ``lxc`` provider: http://bit.ly/vagrant-lxc-precise64-2013-10-23

Other image and providers can be used too. Feel free to report any bugs and
add more links here. In particular,  running tests on cloud hostings is very
encouraged.

First make sure that submodules are up to date::

    git submodule update --init --recursive

You may also checkout specific versions of each of the project in the
``projects`` directory.

Add base box as ``nntest_base``::

    vagrant box add nntest_base <URL>
    make -C projects box PROVIDER=virtualbox

If everything is OK it builds ``projects/nntest.box``. You should add it
as vagrant box ``nntest``:

    vagrant box add nntest projects/nntest.box

Now you may provision test containers.

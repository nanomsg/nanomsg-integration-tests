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

All test cases are in ``cases`` directory. But while running they create a lot
of garbage files, so you should run them from a new directory::

    mkdir -p run/pipes
    cd run/pipes
    ../../bootstrap.py ../../cases/pipes.yaml test_name

This will bootstrap all configs for the test, and print instructions of how
to run the test. Usually it boils down to the following::

    vagrant up --provision
    ./runtest.sh
    vagrant destroy --force
    ./mkreport.sh

Then you can observe the results in ``report.html``.

The ``test_name`` can be discovered either by looking in yaml file or by
running the command with random name, and looking into error output. You may
also tweak the test yaml, especially ``tests`` section to tweak test settings.

.. note:: The recommended way is to create a new directory for each test. You
   may experience some bugs when trying to run same or different test case from
   same directory

.. warning:: Before removing test directory you may need to run
   ``vagrant destroy``. Otherwise vagrant may leave some virtual machines
   running or just lying around and taking disk space


Host Dependencies
=================

Here are the list of base dependencies you should have installed on the host
to run the tests:

* vagrant
* make
* rrdtool
* rsync
* python (probably both 2 and 3 supported, python3 is tested though)
* PyYAML

You also need whatever your vagrant provider needs (e.g. virtualbox itself
by default).

Everything else including nanomsg, and other test software is installed
automatically inside the virtual machines.

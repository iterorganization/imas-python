Benchmarking IMASPy
===================

IMASPy integrates with the `airspeed velocity
<https://asv.readthedocs.io/en/stable/index.html>`_ ``asv`` package for benchmarking.


IMASPy benchmarks
-----------------

IMASPy benchmarks are stored in the ``benchmarks`` folder in the git repository. We can
currently distinguish three types of benchmarks:

Technical benchmarks
    These are for benchmarking features not directly connected to user-interfacing
    functionality. For example benchmarking the time it takes to import the imaspy
    package.

Basic functional benchmarks
    These are for benchmarking functionality with an equivalent feature in the IMAS
    Access Layer HLI. In addition to tracking the performance of the IMASPy features
    over time, we can also benchmark the performance against the traditional HLI.

    For example: putting and getting IDSs.

IMASPy-specific functional benchmarks
    These are for benchmarking functionality without an equivalent feature in the IMAS
    Access Layer HLI. We use these for tracking the IMASPy performance over time.

    For example: data conversion between DD versions.


Running benchmarks (quick and dirty)
------------------------------------

When you have an existing IMASPy installation, you can run the benchmarks like this:

.. code-block:: console

    $ asv run --python=same --quick

.. note:: You need to have ``asv`` installed for this to work, see https://asv.readthedocs.io/en/stable/installing.html

This will execute all benchmarks once in your active python environment. The upside of
executing all benchmarks once is that this won't take very long. The downside is that
``asv`` won't be able to gather statistics (variance) of the run times, so you'll note
that in the output all timings are reported ``±0ms``.

When you remove the ``--quick`` argument, ``asv`` will execute each benchmark multiple
times. This will take longer to execute, but it also gives better statistics.


Interpreting the output
'''''''''''''''''''''''

``asv`` will output the timings of the various benchmarks. Some benchmarks are
parametrized (they are repeated with varying parameters), in which case the output
contains tabular results. Some examples:

.. code-block:: text
    :caption: Example output for a test parametrized in ``hli``

    [ 58.33%] ··· core_profiles.Generate.time_create_core_profiles          ok
    [ 58.33%] ··· ======== ============
                    hli                
                  -------- ------------
                    imas    22.9±0.4μs 
                   imaspy    408±8μs   
                  ======== ============

Here we see the benchmark ``core_profiles.Generate.time_create_core_profiles`` was
repeated for multiple values of ``hli``: once for the ``imas`` HLI, and once for the
``imaspy`` HLI.

Some benchmarks are parametrized in multiple dimensions, as in below example. This
results in a 2D table of results.

.. code-block:: text
    :caption: Example output for a test parametrized in ``hli`` and ``backend``

    [ 70.83%] ··· core_profiles.Get.time_get                                ok
    [ 70.83%] ··· ======== ========== ============ =========
                  --                    backend             
                  -------- ---------------------------------
                    hli        13          14          11   
                  ======== ========== ============ =========
                    imas    75.1±1ms   70.2±0.5ms   207±2ms 
                   imaspy   241±4ms     229±2ms     364±6ms 
                  ======== ========== ============ =========

.. note::
    The backends are listed by their numerical IDS:

    - 11: ASCII backend
    - 12: MDSplus backend
    - 13: HDF5 backend
    - 14: Memory backend


Running benchmarks (advanced)
-----------------------------

Running benchmarks in the quick and dirty way is great during development and for
comparing the performance of IMASPy against the imas HLI. However, ``asv`` can also
track the performance of benchmarks over various commits of IMASPy. Unfortunately this
is a bit more tricky to set up.


Setup advanced benchmarking
'''''''''''''''''''''''''''

First, some background on how ``asv`` tracks performance: it creates an isolated virtual
environment (using the ``virtualenv`` package) for each commit that will be benchmarked.
Then it installs IMASPy inside that envrionment for benchmarking. However, because the
virtual environment is isolated, the ``imas`` package won't be available. We need to
work around it by setting the environment variable ``ASV_PYTHONPATH``:

.. code-block:: console
    :caption: Setting up the ``ASV_PYTHONPATH`` on SDCC

    $ module load IMAS
    $ export ASV_PYTHONPATH="$PYTHONPATH"

.. caution::

    ``imaspy`` must not be available on the ``ASV_PYTHONPATH`` to avoid the interfering
    of two imaspy modules (one on the ``PYTHONPATH``, and the other installed by ``asv``
    in the virtual environment).


Deciding which commits to benchmark
'''''''''''''''''''''''''''''''''''

TODO:
1. Check commits with `git rev-list`, e.g. `git rev-list HEAD^!`
2. Run `asv run ...`, note on benchmarking on not benchmarking on login nodes of SDCC
3. SLURM batch script for running on the compute cluster
4. Showing results

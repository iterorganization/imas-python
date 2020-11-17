Installing IMASPy
=================

IMASPy is a Python package with a compiled component, specifically the
:al_cython:`Cython layer of the IMAS Access Layer (AL) <browse>`. This component
is optional, but necessary to interact with the IMAS-AL, and thus with data stored
to disk by said AL.

IMASPy also needs the :al_lib:`IMAS Python helper functions <browse>`. Currently, both
dependencies are pulled it using :std:doc:`GitPython <gitpython:index>`, until the
:issue:`separate Python HLI parts are available as packages <IMAS-584>`.

.. :std:doc:`Cython <cython:index>` of the 


Python is very flexible, and so is it's install procedure. This is a double-edged sword:
Because of it flexibility, many different install options are available and in use in the
community. For an introduction to the topic, read the
:pypa:`guide to installing Python packaging by the Python Packaging Authority (PyPA) <tutorials/installing-packages/>`.

Installing on the ITER cluster
------------------------------
We assume a clean system. To interact with the AL, we need the IMAS environment
activated. I'm assuming a bash shell for all these commands:

.. code-block:: bash

    module load AL-Python-lib
    module load AL-Cython

This should give us all we need, namely at time of testing:

* ``python`` with a recent version: ``python --version #Python 3.8.2``
* The Python package installer ``pip``:
  ``pip --version #pip 20.0.2 from /work/imas/opt/EasyBuild/software/Python/3.8.2-GCCcore-9.3.0/lib/python3.8/site-packages/pip-20.0.2-py3.8.egg/pip (python 3.8)``

We are all developers, let's install in [pip editable](https://pip.pypa.io/en/stable/reference/pip_install/#options)/[setuptools develop](https://setuptools.readthedocs.io/en/latest/setuptools.html#development-mode) mode. **We are not using PEP517 build isolation to link to the systems numpy.**, **We are not using PyPA's recommended environment management, but instead install into the USER_SITE, this is ~/.local by default.**

.. code-block:: bash

    git clone git@gitlab.com:klimex/imaspy.git
    pip install --user -e imaspy[backends_al,backends_xarray,test]


We should now be able to run the examples

.. code-block:: bash
    python imaspy/examples/read_write_nbi.py

Develop install
^^^^^^^^^^^^^^^

.. note:: Check if this is still needed

pip install --user -e .[backends_al,backends_xarray,test]

Check if you have access to the AL repository. This is currently needed to pull 'secret' dependencies. This will be checked by `pip` too but better to know it now.

* Access to ``libimas.a``, located in ``$IMAS_PREFIX/lib``:
  ``ls $IMAS_PREFIX/lib/libimas #/work/imas/core/IMAS/3.28.1-4.8.3/lib/libimas.a``
  in our ``LD_LIBRARY_PATH=$IMAS_PREFIX/lib:$LD_LIBRARY_PATH``
* A ``UAL_VERSION``, which will be used to pull the low-level AL files from the ITER
  repository. ``echo $UAL_VERSION #4.8.3``

``` bash
(git ls-remote ssh://git@git.iter.org/imas/access-layer.git > /dev/null) && echo 'Connection successful!' || echo 'Connection failed!'
# Connection successful!


Quick primer on Python packages
-------------------------------
A :pypa:`Python package <glossary/#term-import-package>`, commonly just called 'package', is a collection of :pypa:`Python modules <glossary/#term-module>`; reusable pieces of Python code. After installation, these packages are importable in scripts of other users, with the ``import package_name`` statement. On HPC systems, packages available to the user come from the following common locations:

1. From the globally installed Python packages. These are installed by the system administrator (e.g. someone with `sudo` rights). For example on the ITER cluster:

.. code-block:: bash

    module purge
    module load Python/3.6.4-intel-2018a
    python -c 'import site; print(site.getsitepackages())'
    # ['/work/imas/opt/EasyBuild/software/Python/3.6.4-intel-2018a/lib/python3.6/site-packages']

2. From imported modules. These are usually centrally managed and also handled by the system administrator. For example on the ITER cluster:

.. code-block:: bash

    module purge
    module load Python/3.6.4-intel-2018a PyAL
    python -m site
    # sys.path = [
    #   <snip>
    #   '/work/imas/opt/EasyBuild/software/Python/3.6.4-intel-2018a/lib/python3.6/site-packages/numpy-1.14.0-py3.6-linux-x86_64.egg'
    #   <snip>
    # ]

3. From the local user environment, usually in the users' HOME directory:

.. code-block:: bash

    python -c 'import site; print(site.USER_SITE)'
    # /home/ITER/vandepk/.local/lib/python3.6/site-packages

4. From the current working directory. E.g. if I have a file called ``fancy_code.py`` in my current folder, I can call ``from fancy_code import *`` from my other Python files.

Installing a Python package just means putting the Python files somewhere the python binary can find it. It does this by walking down the `sys.path` until a package with the right name is found. See :std:doc:`python:library/importlib`

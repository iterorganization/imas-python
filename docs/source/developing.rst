Developing IMASPy
=================

When developing IMASPy we recommend installation in editable mode.
After cloning the IMASPy repository, run the following command from the project root.

.. code-block:: bash

    pip install -e .[test,docs]

This installs the dependencies for you which are necessary to run the test suite
and to generate the documentation locally.

The test suite can then be run as

.. code-block::bash

    pytest imaspy

And the documentation can be regenerated with

.. code-block::bash

    make -C docs html

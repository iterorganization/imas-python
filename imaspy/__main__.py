# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""Support module to run imaspy as a module:

.. code-block:: bash
    :caption: Options to run imaspy CLI interface

    # Run as a module (implemented in imaspy/__main__.py)
    python -m imaspy

    # Run as "program" (see project.scripts in pyproject.toml)
    imaspy
"""

from imaspy.command.cli import cli

cli()

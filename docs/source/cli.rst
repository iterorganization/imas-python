IMASPy Command Line tool
========================

IMASPy comes with a command line tool: ``imaspy``. This allows you to execute
some tasks without writing Python code:

- ``imaspy convert`` can convert Data Entries (or, optionally, single IDSs from
  a Data Entry) to a different DD version. This command can also be used to
  convert IDSs between different backends.
- ``imaspy print`` can print the contents of an IDS to the terminal.
- ``imaspy version`` shows version information of IMASPy.


Command line tool reference
---------------------------

.. click:: imaspy.command.cli:cli
    :prog: imaspy
    :nested: full
 
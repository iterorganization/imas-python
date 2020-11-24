.. Master "index". This will be converted to a landing index.html by sphinx. We define TOC here, but it'll be put in the sidebar by the theme

===========================
IMASPy Manual
===========================
IMASPy is (yet another) pure-python library to handle arbitrarily nested
data structures. IMASPy is designed for, but not necessarily bound to,
interacting with Interface Data Structures (IDSs) as defined by the
Integrated Modelling & Analysis Suite (IMAS) Data Model.

It provides:

- An easy-to-install and easy-to-get started package by

  * Not requiring an IMAS installation
  * Not strictly requiring matching a Data Dictionary (DD) version
- An pythonic alternative to the IMAS Python High Level Interface (HLI)
- Checking of correctness on assign time, instead of database write time
- Dynamically created in-memory pre-filled data trees from DD XML specifications

For users
=========
* Documentation is WIP! :merge:`4`
* :doc:`iter_cluster`

.. toctree::
   :hidden:
   :caption: Getting Started
   :maxdepth: 2

   self
   installing

README
-----------
The README is best read on :src:`#imaspy`.

For developers
==============

* :doc:`api`
* :doc:`api-hidden`

.. toctree::
   :hidden:
   :caption: API docs

   api
   api-hidden



LICENSE
-------
.. literalinclude:: ../../LICENSE


Sitemap
-------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


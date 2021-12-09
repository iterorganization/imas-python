# IMASPy

IMASPy is (yet another) pure-python library to handle arbitrarily nested
data structures. IMASPy is designed for, but not necessarily bound to,
interacting with Interface Data Structures (IDSs) as defined by the
Integrated Modelling & Analysis Suite (IMAS) Data Model.

It provides:
* An easy-to-install and easy-to-get started package by
  * Not requiring an IMAS installation
  * Not strictly requiring matching a Data Dictionary (DD) version
* An pythonic alternative to the IMAS Python High Level Interface (HLI)
* Checking of correctness on assign time, instead of database write time
* Dynamically created in-memory pre-filled data trees from DD XML specifications

## A word of caution
This package is developed on [ITER bitbucket](https://git.iter.org/projects/IMAS/repos/imaspy).
For user support, contact the IMAS team on the [IMAS user slack](https://imasusers.slack.com),
open a [JIRA issue](https://jira.iter.org/projects/IMAS), or email the support team on imas-support@iter.org.
or open a [JIRA issue](https://jira.iter.org).

## Documentation
Documentation is autogenerated from the source using [Sphinx](http://sphinx-doc.org/)
and can be found at the [ITER sharepoint](https://sharepoint.iter.org/departments/POP/CM/IMDesign/Code%20Documentation/IMASPy-doc/html/index.html)

The documentation can be manually generated by installing sphinx and running:
```bash
make -C docs html
```

### Prerequisites

IMASPy is a standalone python package with optional dependencies. All needed
python packages can be found in `requirements.txt`, and should all be publicly
available. A simple `pip install -r requirements.txt` should take care of everything.

#### Being IMAS DD compatible

To check IMAS DD compatible, one needs the IDS definition XML file. This file
can usually be found at `$IMAS_PREFIX/include/IDSDef.xml` on your IMAS-enabled
system. Otherwise, they can be build from source from the
[ITER IMAS Core Data Dictionary repository](https://git.iter.org/projects/IMAS/repos/data-dictionary/browse)
or, rely on the xml files shipped with IMASPy.

#### Interacting with IMAS AL

Interaction with the IMAS AL is provided by Cython and Python wrappers provided
by the Python High Level Interface. As Cython code, it needs to be compiled on
your local system. First make sure you can access the
[ITER IMAS Access Layer repository](https://git.iter.org/projects/IMAS/repos/access-layer/browse)
using SSH `ssh://git@git.iter.org/imas/access-layer.git`.


## Where does IMASPy live in IMAS ecosystem?
IMASPy tries to fill a slightly different niche than existing tools. It aims
to be an _alternative_ to Python HLI instead of a wrapper. It tries to be
dynamic instead of pre-generated. Is hopes to be extendable instead of
wrappable.

A small, biased, and wildly incomplete of some common IMAS tools, and
where they live with respect to IMASPy.
``` mermaid
classDiagram
  MDSPLUS_DATABASE .. LL_AL : puts
  MDSPLUS_DATABASE .. LL_AL : gets
  MDSPLUS_DATABASE .. LL_HDC : puts
  MDSPLUS_DATABASE .. LL_HDC : gets
  IMAS DD <.. PythonHLI: build dep
  IMAS DD <-- IMASPy:  runtime dep
  LL_HDC <-- HDC_python_bindings : calls
  LL_AL <-- Cython_HLI : calls
  Python_helpers <-- IMASPy: calls
  HDC_python_bindings <.. IMASPy: Could call

  Cython_HLI <-- Python_helpers : calls
  Python_helpers <-- Python HLI: calls

  IMASDD <..  IMASviz_codegen: build dep
  IMASviz_codegen <..  IMASviz: build dep

  PythonHLI <-- OMAS: calls
  OMAS <-- OMFIT: calls
  OMFIT <-- IMASgo : calls

  PythonHLI <-- pyAL: calls
  PythonHLI <-- JINTRAC_WORKFLOWS : calls
  pyAL <-- HnCD_WORKFLOWS : calls
  PythonHLI <-- HnCD_WORKFLOWS : calls
  PythonHLI <-- IMASviz: calls
```

## Contributing

IMASPy is open for contributions! Please open a
[fork](https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html#creating-a-fork)
and create a
[merge request](https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html#merging-upstream)
or request developer access to one of the maintainers.

## Acknowledgments

Inspired and bootstrapped by existing tools, notably the IMAS Python HLI,
IMAS Python workflows, and OMAS.

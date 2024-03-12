# IMASPy

IMASPy is a pure-python library to handle arbitrarily nested data structures.
IMASPy is designed for, but not necessarily bound to, interacting with
Interface Data Structures (IDSs) as defined by the
Integrated Modelling & Analysis Suite (IMAS) Data Model.

It provides:

* An easy-to-install and easy-to-get started package by
  * Not requiring an IMAS installation
  * Not strictly requiring matching a Data Dictionary (DD) version
* An pythonic alternative to the IMAS Python High Level Interface (HLI)
* Checking of correctness on assign time, instead of database write time
* Dynamically created in-memory pre-filled data trees from DD XML specifications

This package is developed on [ITER bitbucket](https://git.iter.org/projects/IMAS/repos/imaspy).
For user support, contact the IMAS team on the [IMAS user slack](https://imasusers.slack.com),
open a [JIRA issue](https://jira.iter.org/projects/IMAS), or email the
support team on <imas-support@iter.org>.

## Installation

### On ITER system, EuroFusion gateway

There is a `module` available on ITER and the Gateway, so you can run

```bash
module load IMASPy
```

IMASPy can work with either Access Layer versions 4 or 5 (the used version is
automatically detected when importing the `imaspy` module). IMASPy still works (with
limited functionality) when no IMAS module is loaded.

### Local

We recommend using a `venv`:

```bash
python3 -m venv ./venv
. venv/bin/activate
```

Then clone this repository, and run `pip install`:

```bash
git clone ssh://git@git.iter.org/imas/imaspy.git
cd imaspy
pip install .
```

If you get strange errors you might want to upgrade your `setuptools` and `pip`.
(you might want to add the `--user` flag to your pip installs when not in a `venv`)

### Development installation

For development an installation in editable mode may be more convenient, and
you will need some extra dependencies to run the test suite and build
documentation.

```bash
pip install -e .[test,docs]
```

Test your installation by trying

```bash
cd ~
python -c "import imaspy; print(imaspy.__version__)"
```

which should return your just installed version number.

### Installation without ITER access

The installation script tries to access the [ITER IMAS Core Data Dictionary repository](https://git.iter.org/projects/IMAS/repos/data-dictionary/browse)
to fetch the latest versions. If you do not have git+ssh access there, you can
try to find this repository elsewhere, and do a `git fetch --tags`.

Alternatively you could try to obtain an `IDSDef.zip` and place it in `~/.config/imaspy/`.

Test your installation by trying

```bash
python -c "import imaspy; factory = imaspy.IDSFactory()"
```
If the following error is raised:
```bash
RuntimeError: Could not find any data dictionary definitions. 
```
Ensure that you have the necessary packages. You can do this by entering `build_DD` in the command line.
Missing packages can include among others: [GitPython](https://github.com/gitpython-developers/GitPython), and Java.

## How to use

```python
import imaspy
factory = imaspy.IDSFactory()
equilibrium = factory.equilibrium()
print(equilibrium)

equilibrium.ids_properties.homogeneous_time = imaspy.ids_defs.IDS_TIME_MODE_HETEROGENEOUS
equilibrium.ids_properties.comment = "testing"

dbentry = imaspy.DBEntry(imaspy.ids_defs.HDF5_BACKEND, "ITER", 1, 1)
dbentry.create()
dbentry.put(equilibrium)

# TODO: find an example with a significant change between versions (rename?)
older_dbentry = imaspy.DBEntry(imaspy.ids_defs.HDF5_BACKEND, "ITER", 1, 1, version="3.35.0")
equilibrium2 = older_root.get("equilibrium")
print(equilibrium2.ids_properties.comment)
```

## Documentation

Documentation is autogenerated from the source using [Sphinx](http://sphinx-doc.org/)
and can be found at the [ITER sharepoint](https://sharepoint.iter.org/departments/POP/CM/IMDesign/Code%20Documentation/IMASPy-doc/index.html)

The documentation can be manually generated by installing sphinx and running:

```bash
make -C docs html
```

## Interacting with IMAS AL

Interaction with the IMAS AL is provided by a Cython interface to the Access Layer.
As Cython code, it needs to be compiled on your local system.
To find the headers, the Access Layer `include` folder needs to be in your `INCLUDE_PATH`. On most HPC systems, a `module load IMAS` is enough.

## Acknowledgments

Inspired and bootstrapped by existing tools, notably the IMAS Python HLI,
IMAS Python workflows, and OMAS.

# IMAS-Python

IMAS-Python is a pure-python library to handle arbitrarily nested data structures.
It is designed for, but not necessarily bound to, interacting with Interface 
Data Structures (IDSs) as defined by the Integrated Modelling & Analysis Suite (IMAS) 
Data Model.


## Install

Install steps are described in the documentation generated from `/docs/source/installing.rst`.

Documentation is autogenerated from the source using [Sphinx](http://sphinx-doc.org/)
and can be found at the [ITER sharepoint](https://sharepoint.iter.org/departments/POP/CM/IMDesign/Code%20Documentation/IMAS-doc/index.html)

The documentation can be manually generated by installing sphinx and running:

```bash
make -C docs html
```


## How to use

```python
import imas
factory = imas.IDSFactory()
equilibrium = factory.equilibrium()
print(equilibrium)

equilibrium.ids_properties.homogeneous_time = imas.ids_defs.IDS_TIME_MODE_HETEROGENEOUS
equilibrium.ids_properties.comment = "testing"

with imas.DBEntry("imas:hdf5?path=./testdb","w") as dbentry:
    dbentry.put(equilibrium)
```

A quick 5 minutes introduction is available in the documentation generated from `/docs/sources/intro.rst`.


## Legal

IMAS-Python is Copyright 2020-2024 ITER Organization, Copyright 2020-2023 Karel Lucas van de 
Plassche <karelvandeplassche@gmail.com>, Copyright 2020-2022 Daan van Vugt <dvanvugt@ignitioncomputing.com>,
and Copyright 2020 Dutch Institute for Fundamental Energy Research <info@differ.nl>.
It is licensed under [LGPL 3.0](LICENSE.txt).


## Acknowledgments

Inspired and bootstrapped by existing tools, notably the IMAS Python HLI,
IMAS Python workflows, and OMAS.

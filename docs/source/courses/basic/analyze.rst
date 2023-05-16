Analyze with IMASPy
===================

.. TODO:: Add content

Load data
---------

I want to read the equilibrium for the whole scenario, and the electron temperature profile at the time slice t=253s of scenario selected above (shot/run/user/database = 134173/106/public/ITER)

.. tabs::
    .. group-tab:: AL4
        .. literalinclude:: al4_snippits/read_whole_equilibrium.py

    .. group-tab:: IMASPy
        .. literalinclude:: imaspy_snippits/read_whole_equilibrium.py

I may want to only read the time array of the equilibrium IDS, to get the time trace of a given scenario (this is how e.g, one can find the index corresponding a specific time slice):

.. tabs::
    .. group-tab:: AL4
        .. literalinclude:: al4_snippits/read_equilibrium_time_array.py

    .. group-tab:: IMASPy
        .. literalinclude:: imaspy_snippits/read_equilibrium_time_array.py


If the data structure is too large and it order to save time and memory, one can decide to read only the Te profile of the core_profiles IDS at t=253s (note: one has to know that it corresponds to index=261 of the core_profiles.time array, which can be found with the method above, assuming that the equilibrium and core_profiles IDSs are defined on the same time array, which is not necessarily the case):

.. tabs::
    .. group-tab:: AL4
        .. literalinclude:: al4_snippits/read_core_profiles_te_timeslice.py

    .. group-tab:: IMASPy
        .. literalinclude:: imaspy_snippits/read_core_profiles_te_timeslice.py


To plot the Te profile read above:

.. tabs::
    .. group-tab:: AL4
        .. literalinclude:: al4_snippits/plot_core_profiles_te_timeslice.py

    .. group-tab:: IMASPy
        .. literalinclude:: imaspy_snippits/plot_core_profiles_te_timeslice.py


Open IMAS database entry
''''''''''''''''''''''''

Load a time slice
'''''''''''''''''

Plot data
---------

Access data
'''''''''''

Get coordinate information
''''''''''''''''''''''''''

Plot data against coordinates
'''''''''''''''''''''''''''''

Plot time-dependent data
------------------------

Load full IDS
'''''''''''''

Create time-dependent plot
''''''''''''''''''''''''''

Transform with IMASPy
=====================

In this part of the course we'll perform a coordinate transformation. Our input data is
in rectilinear :math:`R, Z` coordinates, which we will transform into poloidal polar
coordinates (:math:`\rho_{polar}, \theta`) then store in a separate data entry.

Our strategy for doing this will be:

#. Check which time slices exist
#. The actual processing is done per time slice to limit memory consumption:
   #. Load the time slice
   #. Apply the coordinate transformation
   #. Store the time slice


Check which time slices exist
-----------------------------

.. tabs::

    .. tab:: Exercise

        Load the time array from the ``equilibrium`` IDS in the training data entry.

        .. hint::
            You can use :ref:`lazy loading` to avoid loading all data in memory.
    
    .. tab:: IMASPy

        .. literalinclude:: imaspy_snippets/transform_grid.py
            :start-at: # Open input data entry
            :end-before: # Create output data entry


Load a time slice
-----------------

.. tabs::

    .. tab:: Exercise

        Loop over each available time in the IDS and load the time slice inside the
        loop.

    .. tab:: IMASPy

        .. literalinclude:: imaspy_snippets/transform_grid.py
            :start-at: # Loop over each time slice
            :end-before: # Update comment


Apply the transformation
------------------------

We will apply the transformation of the data as follows:

#.  Load the :math:`R,Z` grid from the time slice
#.  Generate a new :math:`\rho,\theta` grid
#.  Calculate the rectilinear coordinates belonging to the :math:`\rho,\theta` grid:

    .. math::

        R = R_\mathrm{axis} + \rho \cos(\theta)

        Z = Z_\mathrm{axis} + \rho \sin(\theta)

#.  For each data element, interpolate the data on the new grid. We can use
    :py:class:`scipy.interpolate.RegularGridInterpolator` for this.
#.  Finally, we store the new grid (including their rectilinear coordinates) and the
    transformed data in the IDS

.. literalinclude:: imaspy_snippets/transform_grid.py
    :start-at: # Loop over each time slice
    :end-before: # Finally, put the slice to disk


Store a time slice
------------------

.. tabs::

    .. tab:: Exercise

        Store the time slice after the transformation.

    .. tab:: IMASPy

        .. literalinclude:: imaspy_snippets/transform_grid.py
            :start-at: # Create output data entry
            :end-at: output_entry.create()
            :caption: The data entry is created once, outside the time slice loop
        
        .. literalinclude:: imaspy_snippets/transform_grid.py
            :start-at: # Finally, put the slice to disk
            :end-at: output_entry.put_slice
            :caption: Store the time slice inside the loop


Plotting data before and after the transformation
-------------------------------------------------

.. tabs::

    .. tab:: Exercise

        Plot one of the data fields in the :math:`R, Z` plane (original data) and in the
        :math:`\rho,\theta` plane (transformed data) to verify that the transformation
        is correct.

    .. tab:: IMASPy

        .. literalinclude:: imaspy_snippets/transform_grid.py
            :start-at: # Create a plot


Bringing it all together
------------------------

.. literalinclude:: imaspy_snippets/transform_grid.py
    :caption: Source code for the complete exercise

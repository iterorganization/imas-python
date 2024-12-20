IMASPy development and release process
======================================

IMASPy development follows the `Gitflow workflow
<https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow>`_:

1.  New features, bug fixes, etc. are developed in a separate branch. Typically named
    ``feature/<feature_description>``, ``bugfix/IMAS-XXXX``, etc.
2.  When the feature is finished, a Pull Request to the ``develop`` branch is created.
3.  The PR is reviewed and, after approval, changes are merged to ``develop``.
4.  The ``main`` branch is updated only on releases, see below.


Creating an IMASPy release
--------------------------

1.  Create a Pull Request from ``develop`` to ``main``.
2.  Add a change log to the Pull Request, briefly describing new features, bug fixes,
    etc. See, for example, `this PR for version 0.8.0
    <https://git.iter.org/projects/IMAS/repos/imaspy/pull-requests/136/overview>`_.
3.  The PR is reviewed and merged by IO (currently Olivier Hoenen, who also creates the
    release tags).
4.  After the release PR is merged, update the Easybuild configurations for SDCC modules
    in the `easybuild-easyconfigs repository
    <https://git.iter.org/projects/IMEX/repos/easybuild-easyconfigs/browse/easybuild/easyconfigs/i/IMASPy>`_.
    See the next section for more details on how to do this.


Updating and testing the IMASPy Easybuild configuration
-------------------------------------------------------

The following steps can be taken on an SDCC login node.

Configure easybuild
'''''''''''''''''''

First we need to configure easybuild. This only needs to be done once.

-   Create an HTTP access token in Bitbucket with ``PROJECT READ`` and ``REPOSITORY
    READ`` permissions. See this `Bitbucket support page
    <https://confluence.atlassian.com/bitbucketserver0721/http-access-tokens-1115665626.html>`_
    for more details.
-   Create a new text file in your home folder
    ``$HOME/.config/easybuild/secret.txt``. Fill it as follows (replace ``<token>``
    with the token generated in the previous bullet).

    .. code-block:: text
        :caption: ``$HOME/.config/easybuild/secret.txt``

        ^https://git.iter.org::Authorization: Bearer <token>

    Ensure that only you have access to the file, e.g. ``chmod 600
    ~/.config/easybuild/secret.txt``.
-   Create a new configuration file ``$HOME/.config/easybuild/config.cfg`` and fill
    it as follows (replace ``<username>`` with your username):

    .. code-block:: cfg
        :caption: ``$HOME/.config/easybuild/config.cfg``

        [override]
        # Set extra HTTP header Fields when downloading files from URL patterns:
        http-header-fields-urlpat=/home/ITER/<username>/.config/easybuild/secret.txt

        # Set modules flags
        module-syntax=Tcl
        modules-tool=EnvironmentModules
        allow-modules-tool-mismatch=true


Update and test Easybuild configurations
''''''''''''''''''''''''''''''''''''''''

The following steps must be performed for each of the tool chains (currently
``intel-2020b``, ``foss-2020b`` and ``gfbf-2022b``):

1.  Create the ``.eb`` file for the new release.

    a.  Copy the ``.eb`` file from the previous release.
    b.  Update the ``version`` to reflect the just-released version tag.
    c.  If any of the IMASPy dependencies in ``pyproject.toml`` where updated or changed
        since the previous release, update the easybuild dependencies:

        -   ``builddependencies`` contains build-time dependencies which are available
            as a module on SDCC.

            .. note::

                The IMAS module is a build-time dependency only and not a runtime
                dependency. This allows IMASPy users to load the IMASPy module and
                **any** supported IMAS module.

        -   ``dependencies`` contains run-time dependencies which are available as a
            module on SDCC.
        -   ``exts_list`` contains python package dependencies (and potentially
            dependencies of dependencies) which are not available in any of the Python
            modules on SDCC.
    
    d.  Update the checksum of imaspy: download an archive of the IMASPy repository from
        bitbucket. This is easiest to do by copying the following URL, replace
        ``<version>`` with the version tag, and paste it in a web browser:

        .. code-block:: text

            https://git.iter.org/rest/api/latest/projects/IMAS/repos/imaspy/archive?at=refs/tags/<version>&format=tar.gz

        Then, calculate the hash of the downloaded archive with ``sha256sum`` and update
        it in the ``.eb`` file.

2.  Test the easybuild configuration:

    a.  Create an easybuild module, replace ``<eb_file>`` with the filename of the
        ``.eb`` file created in step 1.

        .. code-block:: bash

            module purge
            module load EasyBuild
            eb --rebuild <eb_file>

        If this is unsuccessful, investigate the error and update the ``.eb``
        configuration. A useful environment variable for debugging is ``export
        PIP_LOG=pip.log``, which instructs pip to write logs to the specified file
        (``pip.log`` in this example).
    b.  If the module was successfully installed by easybuild, load it:

        .. code-block:: bash

            module purge
            module use ~/.local/easybuild/modules/all/
            module load IMASPy/<version>-<toolchain>
            module laod IMAS
    
    c.  Sanity check the module, for example by running the ``pytest`` unit tests.

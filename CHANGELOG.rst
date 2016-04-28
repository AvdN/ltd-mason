##########
Change Log
##########

[Unreleased]
============

Added
-----

- ``ltd-mason-travis`` is an alternate version of the ``ltd-mason`` command line app intended to run from a Travis CI environment for non-Eups project documentation. ``ltd-mason-travis``  defers the Sphinx build step to the Travis build setup (.travis.yml).
- Documentation for crafting a :file:`.travis.yml`.
- Added a Developer Workflow guide.
- Added the Change Log and License to the documentation.

[0.1.0] - 2016-03-15
====================

Added
-----

- Initial version that includes an ``ltd-mason`` command line tool to build multi-package EUPS documentation project given a metadata.yaml file.
- Defined a schema for metadata.yaml.
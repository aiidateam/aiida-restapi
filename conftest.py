"""Root-level pytest plugins.

Defined here (rather than in ``tests/conftest.py`` or
``benchmarks/tests/conftest.py``) because defining ``pytest_plugins`` in a
non-top-level conftest affects the entire test suite and is rejected by
newer pytest versions.
"""

pytest_plugins = ['aiida.tools.pytest_fixtures']

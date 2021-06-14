# Developer guide

## Running the tests

The following will discover and run all unit test:

    pip install -e .[testing]
    pytest -v

Or via [tox](https://tox.readthedocs.io) in an automated virtual environment (see the tox.ini file):

    tox

## Automatic coding style checks

Enable enable automatic checks of code sanity and coding style:

    pip install -e .[pre-commit]
    pre-commit install

After this, the [black](https://black.readthedocs.io) formatter, the [pylint](https://www.pylint.org/) linter and the [pylint](https://www.pylint.org/) code analyzer will run at every commit.

If you ever need to skip these pre-commit hooks, just use:

    git commit -n

## Continuous integration

`aiida-restapi` comes with a `.github` folder that contains continuous integration tests on every commit using `GitHub Actions <https://github.com/features/actions>`_. It will:

1. run all tests for the `django` ORM
1. build the documentation
1. check coding style and version number (not required to pass by default)

## Building the documentation

 1. Install the `docs` extra:

        pip install -e .[docs]

 1. Edit the individual documentation pages:

        docs/source/index.rst
        docs/source/developer_guide/index.rst
        docs/source/user_guide/index.rst
        docs/source/user_guide/get_started.rst
        docs/source/user_guide/tutorial.rst

 1. Use [Sphinx] to generate the html documentation:

        cd docs
        make

Check the result by opening `build/html/index.html` in your browser.

## Publishing the documentation

Once you're happy with your documentation, it's easy to host it online on [ReadTheDocs]:

 #. Create an account on [ReadTheDocs]

 #. Import your `aiida-restapi` repository (preferably using `aiida-restapi` as the project name)

The documentation is now available at [aiida-restapi.readthedocs.io](http://aiida-restapi.readthedocs.io/).

## PyPI release

Your plugin is ready to be uploaded to the [Python Package Index](https://pypi.org/).
Just register for an account and:

    pip install twine
    python setup.py sdist bdist_wheel
    twine upload dist/*

After this, you (and everyone else) should be able to:

    pip install aiida-restapi

You can also enable *automatic* deployment of git tags to the python package index:
simply generate a `PyPI API token <https://pypi.org/help/#apitoken>`_ for your PyPI account and add it as a secret to your GitHub repository under the name `pypi_token` (Go to Settings -> Secrets).

:::{note}
When updating the plugin package to a new version, remember to update the version number both in `setup.json` and `aiida_restapi/__init__.py`.
:::

[ReadTheDocs]: https://readthedocs.org/
[Sphinx]: https://www.sphinx-doc.org/en/master/

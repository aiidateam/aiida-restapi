[![Build Status](https://github.com/aiidateam/aiida-restapi/workflows/ci/badge.svg?branch=master)](https://github.com/aiidateam/aiida-restapi/actions)
[![Coverage Status](https://codecov.io/gh/aiidateam/aiida-restapi/branch/master/graph/badge.svg?token=zLdnsxfR3v)](https://codecov.io/gh/aiidateam/aiida-restapi)
[![Docs status](https://readthedocs.org/projects/aiida-restapi/badge)](http://aiida-restapi.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-restapi.svg)](https://badge.fury.io/py/aiida-restapi)

# aiida-restapi

AiiDA REST API for data queries and workflow management.

Uses [`pydantic`](https://pydantic-docs.helpmanual.io/) for models/validation and [`fastapi`](https://fastapi.tiangolo.com/) for the ASGI application.
Serve e.g. using [`uvicorn`](https://www.uvicorn.org/).

## Features

 * `/users` (GET/POST) and `/users/<id>` (GET) endpoints
 * Authentication via [JSON web tokens](https://jwt.io/introduction) (see `test_auth.py` for the flow; also works via interactive docs)
 * `User` `pydantic` model for validation
 * Automatic documentation at `http://127.0.0.1:8000/docs`
 * Full specification at `http://127.0.0.1:8000/openapi.json`

## Installation

```shell
pip install aiida-restapi[auth]
```

## Usage

```shell
# start rest api
uvicorn aiida_restapi:app

# start rest api and reload for changes (for development)
uvicorn aiida_restapi:app --reload
```

By default all endpoints of the REST API are available.
The API can be made *read-only* by setting the `read_only` configuration settings to `True`.
This can either be done by setting the environment variable:
```bash
export READ_ONLY=True
```
or by adding the following to the `.env` file:
```ini
read_only=true
```
When the API is read-only, all `DELETE`, `PATCH`, `POST` and `PUT` requests will result in a `405 - Method Not Allowed` response.

## Examples

See the [examples](https://github.com/aiidateam/aiida-restapi/tree/master/examples) directory.

## Development

```shell
git clone https://github.com/aiidateam/aiida-restapi .
cd aiida-restapi
```

### Setting up pre-commit

We use pre-commit to take care for the formatting, type checking and linting.
```shell
pip install -e .[pre-commit]  # install extra dependencies
pre-commit run # running pre-commit on changes
pre-commit run --all-files # running pre-commit on every file
pre-commit run pylint --all-files # run only the linter on every file
```
One can also set up pre-commit to be run on every commit
```shell
pre-commit install
# pre-commit uninstall # to disable it again
```

### Running tests

With tox the tests can be run
```shell
pip install tox
tox -e py311 # run all tests for Python 3.11
tox -av # see all supported environments
```
tox will creat a custom environment to run the tests in. If you want to run the
tests inside your current environment
```shell
pip install -e .[testing]  # install extra dependencies
pytest -v
```

See the [developer guide](http://aiida-restapi.readthedocs.io/en/latest/developer_guide/index.html) for more information.

## License

MIT

## Contact

leopold.talirz@gmail.com
chrisj_sewell@hotmail.com

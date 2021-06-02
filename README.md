[![Build Status](https://github.com/aiidateam/aiida-restapi/workflows/ci/badge.svg?branch=master)](https://github.com/aiidateam/aiida-restapi/actions)
[![Coverage Status](https://coveralls.io/repos/github/aiidateam/aiida-restapi/badge.svg?branch=master)](https://coveralls.io/github/aiidateam/aiida-restapi?branch=master)
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

## Development

```shell
git clone https://github.com/aiidateam/aiida-restapi .
cd aiida-restapi
pip install -e .[pre-commit,testing]  # install extra dependencies
pre-commit install  # install pre-commit hooks
pytest -v  # discover and run all tests
```

See the [developer guide](http://aiida-restapi.readthedocs.io/en/latest/developer_guide/index.html) for more information.

## License

MIT

## Contact

leopold.talirz@gmail.com
chrisj_sewell@hotmail.com

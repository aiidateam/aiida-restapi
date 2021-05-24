[![Build Status](https://github.com/aiidateam/aiida-restapi/workflows/ci/badge.svg?branch=master)](https://github.com/aiidateam/aiida-restapi/actions)
[![Coverage Status](https://coveralls.io/repos/github/aiidateam/aiida-restapi/badge.svg?branch=master)](https://coveralls.io/github/aiidateam/aiida-restapi?branch=master)
[![Docs status](https://readthedocs.org/projects/aiida-restapi/badge)](http://aiida-restapi.readthedocs.io/)
[![PyPI version](https://badge.fury.io/py/aiida-restapi.svg)](https://badge.fury.io/py/aiida-restapi)

# aiida-restapi

AiiDA REST API for data queries and workflow managment.

## Features

 * `/users` and `/users/<id>` endpoints
 * `User` schema for validation
## Installation

```shell
pip install aiida-restapi
```

## Usage

```shell
# start rest api
uvicorn aiida_restapi:app

# start rest api and reload for changes (for development)
uvicorn aiida_restapi:app --reload-dir aiida_restapi
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

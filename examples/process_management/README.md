# Process Management

## Description

This example shows how to manage processes over the web API, such as checking the status and retrieving outputs.
First, the example submits an `ArithmeticAddCalculation` (a calculation plugin that ships with `aiida-core`) to the daemon.
Then, the status of the calculation is queried for and when it is done, the final results are retrieved.

## Instructions

### Server

1. Install `aiida-restapi`:

    ```bash
    pip install aiida-restapi[auth]
    ```

1. Start the web API server:

    ```bash
    uvicorn aiida_restapi:app
    ```

1. Configure an `InstalledCode` to run the `core.arithmetic.add` plugin on a `Computer`:

    ```bash
    verdi computer setup -n -L localhost -H localhost -T core.local -S core.direct -w /tmp
    verdi computer configure core.local localhost -n
    verdi code create core.code.installed \
        --non-interactive \
        --label 'bash' \
        --computer localhost \
        --filepath-executable /bin/bash \
        --default-calc-job-plugin 'core.arithmetic.add'
    ```

1. Start the daemon

    ```bash
    verdi daemon start
    ```


### Client

1. Install Python prerequisites:

    ```bash
    pip install click requests
    ```

1. Execute the example script:

    ```bash
    ./script.py
    ```

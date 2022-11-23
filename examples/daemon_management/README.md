# Process Management

## Description

This example shows how to manage the daemon over the web API, such as:

* Getting the daemon status
* Starting the daemon
* Stopping the daemon


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


### Client

1. Install Python prerequisites:

    ```bash
    pip install click requests
    ```

1. Execute the example script:

    ```bash
    ./script.py
    ```

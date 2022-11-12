# Submission of `PwCalculation` or `PwBaseWorkChain`

## Description

This example shows how to run a web API server configured to run Quantum ESPRESSO pw.x calculations.
In particular, it will run an SCF calculation on a silicon crystal structure.
The file `script.py` is a Python script that acts as the client and performs the following actions:

    1. Send an authentication request to obtain an access token
    1. Create inputs for the process to launch: structure, parameters, k-points
    1. Obtain the UUIDs of pseudopotentials to use
    1. Submit a `PwCalculation` or `PwBaseWorkChain` with a certain set of inputs.


## Instructions

### Server

1. Install [Quantum ESPRESSO](https://www.quantum-espresso.org/faq/faq-installation/)
1. Install `aiida-restapi`:

    ```bash
    pip install aiida-restapi[auth]
    ```

1. Install `aiida-quantumespresso`:

    ```bash
    pip install aiida-quantumespresso
    ```

    and follow [the instructions](https://aiida-quantumespresso.readthedocs.io/en/latest/installation/index.html#setup) to setup a computer, code and pseudo potentials.

1. Start the daemon:

    ```bash
    verdi daemon start
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

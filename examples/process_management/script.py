#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script to demonstrate process management over the web API."""
from __future__ import annotations

import os
import time
import typing as t

import click
import requests

BASE_URL = "http://127.0.0.1:8000"


def echo_error(message: str) -> None:
    """Echo the message prefixed with ``Error`` in bold red.

    :param message: The error message to echo.
    """
    click.echo(click.style("Error: ", fg="red", bold=True), nl=False)
    click.echo(message)


def request(
    url,
    json: dict[str, t.Any] | None = None,
    data: dict[str, t.Any] | None = None,
    method="POST",
) -> dict[str, t.Any] | None:
    """Perform a request to the web API of ``aiida-restapi``.

    If the ``ACCESS_TOKEN`` environment variable is defined, it is passed in the ``Authorization`` header.

    :param url: The relative URL path without leading slash, e.g., `nodes`.
    :param json: A JSON serializable dictionary to send in the body of the request.
    :param data: Dictionary, list of tuples, bytes, or file-like object to send in the body of the request.
    :param method: The request method, POST by default.
    :returns: The response in JSON or ``None``.
    """
    access_token = os.getenv("ACCESS_TOKEN", None)

    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}
    else:
        headers = {}

    response = requests.request(  # pylint: disable=missing-timeout
        method, f"{BASE_URL}/{url}", json=json, data=data, headers=headers
    )

    try:
        response.raise_for_status()
    except requests.HTTPError:
        results = response.json()

        echo_error(f"{response.status_code} {response.reason}")

        if "detail" in results:
            echo_error(results["detail"])

        for error in results.get("errors", []):
            click.echo(error["message"])

        return None
    return response.json()


def authenticate(
    username: str = "johndoe@example.com", password: str = "secret"
) -> str | None:
    """Authenticate with the web API to obtain an access token.

    Note that if authentication is successful, the access token is stored in the ``ACCESS_TOKEN`` environment variable.

    :param username: The username.
    :param password: The password.
    :returns: The access token or ``None`` if authentication was unsuccessful.
    """
    results = request("token", data={"username": username, "password": password})

    if results:
        access_token = results["access_token"]
        os.environ["ACCESS_TOKEN"] = access_token
        return access_token

    return None


def create_node(entry_point: str, attributes: dict[str, t.Any]) -> str | None:
    """Create a ``Node`` and return the UUID if successful or ``None`` otherwise.

    :param entry_point: The entry point name of the node type to create.
    :param attributes: The attributes to set.
    :returns: The UUID of the created node or ``None`` if it failed.
    """
    data = {
        "entry_point": entry_point,
        "attributes": attributes,
    }
    result = request("nodes", data)

    if result:
        return result["uuid"]

    return None


def get_code(default_calc_job_plugin: str) -> dict[str, t.Any] | None:
    """Return a code that has the given default calculation job plugin.

    Returns the first code that is matched.

    :param default_calc_job_plugin: The default calculation job plugin the code should have.
    :raises ValueError: If no code could be found.
    """
    variables = {"default_calc_job_plugin": default_calc_job_plugin}
    query = """
        {
            nodes(filters: "node_type ILIKE 'data.core.code.installed.InstalledCode%'") {
                rows {
                    uuid
                    label
                    attributes
                }
            }
        }
    """
    results = request("graphql", {"query": query, "variables": variables})

    if results is None:
        return None

    node = None

    for row in results["data"]["nodes"]["rows"]:
        if row["attributes"]["input_plugin"] == default_calc_job_plugin:
            node = row

    if node is None:
        raise ValueError(
            f"No code with default calculation job plugin `{default_calc_job_plugin}` found."
        )

    return node


def get_outputs(process_id: int) -> dict[str, t.Any]:
    """Return a dictionary of the outputs of the process with the given ID.

    :param process_id: The ID of the process.
    :return: Dictionary of the outputs where keys are link labels and values are dictionaries containing the node's uuid
        and attributes.
    """
    query = """
        query function($process_id: Int) {
            node(id: $process_id) {
                outgoing {
                    rows {
                        node {
                            uuid
                            attributes
                        }
                        link {
                            label
                        }
                    }
                }
            }
        }
    """
    variables = {"process_id": process_id}
    results = request("graphql", {"query": query, "variables": variables})

    outputs = {}

    for value in results["data"]["node"]["outgoing"]["rows"]:
        link_label = value["link"]["label"]
        outputs[link_label] = {
            "uuid": value["node"]["uuid"],
            "attributes": value["node"]["attributes"],
        }

    return outputs


@click.command()
def main():
    """Authenticate with the web API and submit an ``ArithmeticAddCalculation``."""
    token = authenticate()

    if token is None:
        echo_error("Could not authenticate with the API, aborting")
        return

    # Inputs for a ``ArithmeticAddCalculation``
    inputs = {
        "label": "Launched over the web API",
        "process_entry_point": "aiida.calculations:core.arithmetic.add",
        "inputs": {
            "code.uuid": get_code("core.arithmetic.add")["uuid"],
            "x.uuid": create_node("core.int", {"value": 1}),
            "y.uuid": create_node("core.int", {"value": 1}),
        },
    }

    results = request("processes", json=inputs)
    click.echo(f'Successfuly submitted process with pk<{results["id"]}>')

    process_id = results["id"]

    while True:
        results = request(f"processes/{process_id}", method="GET")
        process_state = results["attributes"]["process_state"]

        if process_state in ["finished", "excepted", "killed"]:
            break

        time.sleep(2)

    click.echo(f"Calculation terminated with state `{process_state}`")

    results = get_outputs(process_id)

    click.echo("Output nodes:")
    for key, value in results.items():
        click.echo(f"* {key}: UUID<{value['uuid']}>")

    click.echo(f"Computed sum: {results['sum']['attributes']['value']}")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter

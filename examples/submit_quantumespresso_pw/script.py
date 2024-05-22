#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script to submit a ``PwCalculation`` or ``PwBaseWorkChain`` over the web API."""
from __future__ import annotations

import os
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


def get_pseudo_family_pseudos(pseudo_family_label: str) -> dict[str, t.Any] | None:
    """Return the pseudo potentials in the given family.

    :param pseudo_family_label: The label of the pseudopotential family.
    :returns: The pseudopotential family and the pseudos it contains.
    """
    variables = {"label": pseudo_family_label}
    query = """
        query function($label: String) {
            group(label: $label) {
                uuid
                label
                nodes {
                    rows {
                        uuid
                        attributes
                    }
                }
            }
        }
    """
    results = request("graphql", {"query": query, "variables": variables})

    if results:
        return results["data"]["group"]

    return None


def get_pseudo_for_element(
    pseudo_family_label: str, element: str
) -> dict[str, t.Any] | None:
    """Return the pseudo potential for a given pseudo potential family and element.

    :param pseudo_family_label: The label of the pseudopotential family.
    :param element: The element for which to retrieve a pseudopotential.
    :returns: The pseudopotential if found, or ``None`` otherwise.
    """
    family = get_pseudo_family_pseudos(pseudo_family_label)

    if family is None:
        return None

    pseudo = None

    for row in family["nodes"]["rows"]:
        if row["attributes"]["element"] == element:
            pseudo = row
            break

    return pseudo


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


@click.command()
@click.option(
    "--workchain",
    is_flag=True,
    help="Submit a ``PwBaseWorkChain`` instead of a ``PwCalculation``.",
)
def main(workchain):
    """Authenticate with the web API and submit a ``PwCalculation`` or ``PwBaseWorkChain``."""
    token = authenticate()

    if token is None:
        echo_error("Could not authenticate with the API, aborting")
        return

    kpoints = {"mesh": [2, 2, 2], "offset": [0, 0, 0]}
    parameters = {
        "CONTROL": {
            "calculation": "scf",
        },
        "SYSTEM": {
            "ecutwfc": 30,
            "ecutrho": 240,
        },
    }

    structure = {
        "cell": [[0.0, 2.715, 2.715], [2.715, 0.0, 2.715], [2.715, 2.715, 0.0]],
        "kinds": [{"mass": 28.085, "name": "Si", "symbols": ["Si"], "weights": [1.0]}],
        "pbc1": True,
        "pbc2": True,
        "pbc3": True,
        "sites": [
            {"kind_name": "Si", "position": [0.0, 0.0, 0.0]},
            {"kind_name": "Si", "position": [1.3575, 1.3575, 1.3575]},
        ],
    }

    code_uuid = get_code("quantumespresso.pw")["uuid"]
    structure_uuid = create_node("core.structure", structure)
    parameters_uuid = create_node("core.dict", parameters)
    kpoints_uuid = create_node("core.array.kpoints", kpoints)
    pseudo_si_uuid = get_pseudo_for_element("SSSP/1.2/PBE/efficiency", "Si")["uuid"]

    if workchain:
        # Inputs for a ``PwBaseWorkChain`` to compute SCF of Si crystal structure
        inputs = {
            "label": "PwCalculation over REST API",
            "process_entry_point": "aiida.workflows:quantumespresso.pw.base",
            "inputs": {
                "kpoints.uuid": kpoints_uuid,
                "pw": {
                    "code.uuid": code_uuid,
                    "structure.uuid": structure_uuid,
                    "parameters.uuid": parameters_uuid,
                    "pseudos": {
                        "Si.uuid": pseudo_si_uuid,
                    },
                },
            },
        }
    else:
        # Inputs for a ``PwCalculation`` to compute SCF of Si crystal structure
        inputs = {
            "label": "PwCalculation over REST API",
            "process_entry_point": "aiida.calculations:quantumespresso.pw",
            "inputs": {
                "code.uuid": code_uuid,
                "structure.uuid": structure_uuid,
                "parameters.uuid": parameters_uuid,
                "kpoints.uuid": kpoints_uuid,
                "pseudos": {
                    "Si.uuid": pseudo_si_uuid,
                },
            },
        }

    results = request("processes", json=inputs)
    click.echo(f'Successfuly submitted process with pk<{results["id"]}>')


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter

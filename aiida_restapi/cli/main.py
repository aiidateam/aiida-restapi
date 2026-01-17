import os

import click
import uvicorn


@click.group()
def cli() -> None:
    """AiiDA REST API management CLI."""


@cli.command()
@click.option('--host', default='127.0.0.1', show_default=True)
@click.option('--port', default=8000, show_default=True, type=int)
@click.option('--read-only', is_flag=True)
@click.option('--watch', is_flag=True)
def start(read_only: bool, watch: bool, host: str, port: int) -> None:
    """Start the AiiDA REST API service."""

    os.environ['AIIDA_RESTAPI_READ_ONLY'] = '1' if read_only else '0'

    click.echo(f'Starting REST API (read_only={read_only}, watch={watch}) on {host}:{port}')

    uvicorn.run(
        'aiida_restapi.main:create_app',
        host=host,
        port=port,
        reload=watch,
        reload_dirs=['aiida_restapi'],
        factory=True,
    )

import click
import uvicorn

from aiida_restapi.main import create_app


@click.group()
def cli() -> None:
    """AiiDA REST API management CLI."""
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', show_default=True, help='Host to bind.')
@click.option('--port', default=8000, show_default=True, type=int, help='Port to bind.')
@click.option('--read-only', is_flag=True, help='Run the REST API in read-only mode.')
def start(read_only: bool, host: str, port: int) -> None:
    """Start the AiiDA REST API service."""
    click.echo(f'Starting REST API (read_only={read_only}) on {host}:{port}')
    app = create_app(read_only=read_only)
    uvicorn.run(app, host=host, port=port)

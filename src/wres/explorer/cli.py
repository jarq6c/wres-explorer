"""Launch the dashboard from a CLI."""
import click
from .dashboard import Dashboard

@click.command()
def run() -> None:
    """
    Visualize and explore output from WRES CSV2 formatted files.

    Run "wres-explorer" from the command-line, ctrl+c to stop the server.:
    """
    # Start interface
    Dashboard("WRES CSV Explorer").serve()

if __name__ == "__main__":
    run()

"""Launch the dashboard from a CLI."""
import click
from .dashboard import serve_dashboard

@click.command()
def run() -> None:
    """
    Visualize and explore output from WRES CSV2 formatted files.

    Run "wres-explorer" from the command-line, ctrl+c to stop the server.:
    """
    # Start interface
    serve_dashboard()

if __name__ == "__main__":
    run()

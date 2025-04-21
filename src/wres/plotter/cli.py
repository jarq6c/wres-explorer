import click
import pandas as pd

@click.command()
@click.argument(
    "filepath",
    nargs=1,
    type=click.Path(exists=True),
    required=False)
def run(filepath: click.Path = None) -> None:
    """
    Visualize metrics output from WRES CSV2 formatted output.

    Example:

    wres-plotter evaluation.csv.gz
    """
    if filepath is None:
        return
    df = pd.read_csv(filepath, dtype=str)
    print(df.head())

if __name__ == "__main__":
    run()

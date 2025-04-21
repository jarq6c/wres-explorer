import click
from .data import load_dataframe

import panel as pn
pn.extension("plotly")
pn.extension('tabulator')

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
    df = load_dataframe(filepath)

    data_table = pn.Column(
        pn.pane.Markdown("Data"),
        pn.widgets.Tabulator(
            df,
            show_index=False,
            disabled=True,
            width=1280
    ))
    files = pn.widgets.FileSelector(
        directory="./",
        file_pattern="*.csv.gz",
        only_files=True,
        value=[str(filepath)]
        )
    tabs = pn.Tabs()
    tabs.append(("File Selector", files))
    tabs.append(("Data", data_table))

    dashboard = pn.template.BootstrapTemplate(title="WRES Plotter")
    dashboard.main.append(tabs)
    pn.serve(dashboard.servable())

if __name__ == "__main__":
    run()

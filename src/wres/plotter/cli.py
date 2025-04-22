import click
import pandas as pd
from .data import load_dataframes

import param
import panel as pn
pn.extension("plotly")
pn.extension('tabulator')

class DataManager(param.Parameterized):
    filepaths = param.MultiFileSelector(path="**/*.csv.gz")
    load_data = param.Action(
        lambda x: x.param.trigger("load_data"),
        doc="Load data"
        )

    @param.depends("load_data")
    def view(self):
        if self.filepaths is None or len(self.filepaths) == 0:
            df = pd.DataFrame({"message": ["no data loaded"]})
        else:
            try:
                df = load_dataframes(self.filepaths)
            except pd.errors.ParserError:
                df = pd.DataFrame({"message": ["parsing error"]})

        return pn.widgets.Tabulator(
            df,
            show_index=False,
            disabled=True,
            width=1280,
            height=720
        )

@click.command()
def run() -> None:
    """
    Visualize and explore metrics output from WRES CSV2 formatted output.

    Example:

    wres-explorer
    """
    # Start interface
    controls = DataManager()
    tabs = pn.Tabs()
    tabs.append(("File Selector", controls.param))
    tabs.append(("Data", controls.view))

    dashboard = pn.template.BootstrapTemplate(title="WRES Explorer")
    dashboard.main.append(tabs)
    pn.serve(dashboard.servable())

if __name__ == "__main__":
    run()

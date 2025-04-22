import click
from .data import load_dataframes

import panel as pn
pn.extension("plotly")
pn.extension('tabulator')

class WRESExplorer:
    def __init__(self, filepaths: list[str] | None = None):
        # Main dashboard
        self.dashboard = pn.template.BootstrapTemplate(title="WRES Explorer")
        self.tabs = pn.Tabs()
        self.dashboard.main.append(self.tabs)

        # File selector tab
        file_selector = pn.widgets.FileSelector(
            directory="./",
            file_pattern="*.csv.gz",
            only_files=True,
            value=[] if filepaths is None else filepaths
            )
        load_button = pn.widgets.Button(
            name="Load Data",
            button_type="primary",
            width=200
        )
        file_tab = pn.Column(
            file_selector,
            load_button
        )
        self.tabs.append(("File Selector", file_tab))

    def serve(self):
        pn.serve(self.dashboard.servable())

@click.command()
@click.argument(
    "filepaths",
    nargs=-1,
    required=False)
def run(filepaths: tuple[str] = None) -> None:
    """
    Visualize and explore metrics output from WRES CSV2 formatted output.

    Example:

    wres-explorer evaluation_1.csv.gz evaluation_2.csv.gz
    """
    # Start interface
    wres_explorer = WRESExplorer(list(filepaths))
    wres_explorer.serve()
    
    # df = load_dataframes(filepaths)

    # data_table = pn.widgets.Tabulator(
    #     df,
    #     show_index=False,
    #     disabled=True,
    #     width=1280
    # )
    # print(data_table.value)
    # return

    # # File selector tab
    # file_selector = pn.widgets.FileSelector(
    #     directory="./",
    #     file_pattern="*.csv.gz",
    #     only_files=True,
    #     value=list(filepaths)
    #     )
    # load_button = pn.widgets.Button(
    #     name="Load Data",
    #     button_type="primary",
    #     width=200
    # )
    # file_tab = pn.Column(
    #     file_selector,
    #     load_button
    # )

    # # Data table tab


    # # Tabs
    # tabs = pn.Tabs()
    # tabs.append(("File Selector", file_tab))
    # # tabs.append(("Data", data_table))

    # dashboard = pn.template.BootstrapTemplate(title="WRES Explorer")
    # dashboard.main.append(tabs)
    # pn.serve(dashboard.servable())

if __name__ == "__main__":
    run()

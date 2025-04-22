import click
import pandas as pd
import geopandas as gpd
from .data import load_dataframes

import plotly.graph_objects as go
import param
import panel as pn
pn.extension("plotly")
pn.extension("tabulator")

class DataManager(param.Parameterized):
    filepaths = param.MultiFileSelector(path="**/**/*.csv.gz")
    load_data = param.Action(
        lambda x: x.param.trigger("load_data"),
        doc="Load data"
        )
    data: pd.DataFrame | None = None

    @param.depends("load_data")
    def data_table(self):
        if self.filepaths is None or len(self.filepaths) == 0:
            self.data = pd.DataFrame({"message": ["no data loaded"]})
        else:
            try:
                self.data = load_dataframes(self.filepaths)
            except pd.errors.ParserError:
                self.data = pd.DataFrame({"message": ["parsing error"]})
            except KeyError:
                self.data = pd.DataFrame({"message": ["column error"]})

        return pn.widgets.Tabulator(
            self.data,
            show_index=False,
            disabled=True,
            width=1280,
            height=720
        )

    @param.depends("load_data")
    def mapper(self):
        if "LEFT FEATURE NAME" not in self.data:
            return pn.widgets.Tabulator(
                self.data,
                show_index=False,
                disabled=True,
                width=1280,
                height=720
            )
        sites = self.data.drop_duplicates(subset="LEFT FEATURE NAME")

        usgs_site_code = pn.widgets.AutocompleteInput(
            name="USGS Site Code",
            options=sites["LEFT FEATURE NAME"].tolist(),
            placeholder="Select USGS Site Code",
            search_strategy="includes"
        )

        geometry = gpd.GeoSeries.from_wkt(
            sites["LEFT FEATURE WKT"].astype(str))
        site_map = go.Scattermap(
            lat=geometry.y,
            lon=geometry.x,
            mode='markers',
            marker=dict(
                size=15,
                color="cyan"
                ),
            name="Gauges",
            legendgroup="site_plots",
            legendgrouptitle_text="Site Info"
            )
        fig = go.Figure()
        fig.add_trace(site_map)
        fig.update_layout(
            map=dict(
                style="satellite-streets",
                center={"lat": geometry.y.mean(), "lon": geometry.x.mean()},
                zoom=2
            )
        )
        return pn.Column(usgs_site_code, pn.pane.Plotly(fig))

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
    tabs.append(("Data", controls.data_table))
    tabs.append(("Map", controls.mapper))

    dashboard = pn.template.BootstrapTemplate(title="WRES Explorer")
    dashboard.main.append(tabs)
    pn.serve(dashboard.servable())

if __name__ == "__main__":
    run()

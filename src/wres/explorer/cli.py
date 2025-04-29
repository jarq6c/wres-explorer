import click
import panel as pn
from panel.template import BootstrapTemplate
import pandas as pd
import plotly.graph_objects as go
from .data import DataManager

pn.extension("tabulator")
pn.extension("plotly")

class Widgets:
    """
    Widgets for the dashboard.
    
    Attributes
    ----------
    file_selector: pn.widgets.FileSelector
        File selector widget for selecting CSV files.
    load_data_button: pn.widgets.Button
        Button to load/reload data.
    left_feature_selector: pn.widgets.AutocompleteInput
        Autocomplete input for selecting left feature.
    right_feature_selector: pn.widgets.AutocompleteInput
        Autocomplete input for selecting right feature.
    map_selector: pn.pane.Plotly
        Pane for displaying the map of features.
    description_pane: pn.pane.Markdown
        Pane for displaying feature descriptions.
    selected_metric: pn.widgets.Select
        Select widget for selecting metrics.
    metrics_pane: pn.pane.Plotly
        Pane for displaying metrics plots.
    """
    def __init__(self):
        self.file_selector = pn.widgets.FileSelector(
            directory="./",
            file_pattern="*.csv.gz",
            only_files=True,
            value=[]
        )
        self.load_data_button = pn.widgets.Button(
            name="Load/Reload Data",
            button_type="primary"
        )
        self.left_feature_selector = pn.widgets.AutocompleteInput(
            name="LEFT FEATURE NAME",
            options=[],
            search_strategy="includes",
            placeholder=f"Select LEFT FEATURE NAME"
        )
        self.right_feature_selector = pn.widgets.AutocompleteInput(
            name="RIGHT FEATURE NAME",
            options=[],
            search_strategy="includes",
            placeholder=f"Select RIGHT FEATURE NAME"
        )
        self.description_pane = pn.pane.Markdown(
            "LEFT FEATURE DESCRIPTION<br>"
            "No data loaded"
        )
        self.map_selector = pn.pane.Plotly()
        self.selected_metric = pn.widgets.Select(
            name="Select Metric",
            options=[]
        )
        self.metrics_pane = pn.pane.Plotly()
    
    @staticmethod
    def build_metrics_table(data: pd.DataFrame) -> None:
        """
        Build a metrics table with the provided data.
        
        Parameters
        ----------
        data: pd.DataFrame
            Data to display in the metrics table.
        """
        return pn.widgets.Tabulator(
            data,
            show_index=False,
            disabled=True,
            width=1280,
            height=720
        )

class Layout:
    """
    Layout for the dashboard.
    
    Attributes
    ----------
    widgets: Widgets
        Instance of Widgets to create the layout.
    tabs: pn.Tabs
        Dashboard tabs.
    template: pn.template
        Servable dashboard with widgets laid out.
    """
    def __init__(self, title: str, widgets: Widgets):
        """
        Initialize the layout of the dashboard.
        
        Parameters
        ----------
        title: str
            Dashboard title.
        widgets: Widgets
            Instance of Widgets to create the layout.
        """
        self.widgets = widgets
        self.tabs = pn.Tabs()
        self.add_tab(
            "File Selector",
            pn.Column(self.widgets.file_selector, self.widgets.load_data_button)
            )
        self.add_tab(
            "Metrics Table",
            self.widgets.build_metrics_table(
                pd.DataFrame({"message": ["no data loaded"]})
        ))
        self.add_tab(
            "Feature Selector",
            pn.Row(
                pn.Column(
                    self.widgets.left_feature_selector,
                    self.widgets.right_feature_selector,
                    self.widgets.description_pane
                    ),
                self.widgets.map_selector
            )
        )
        self.add_tab(
            "Metrics Plots",
            pn.Row(
                pn.Column(
                    self.widgets.description_pane,
                    self.widgets.selected_metric
                ),
                self.widgets.metrics_pane
            )
        )
        self.template = BootstrapTemplate(title=title)
        self.template.main.append(self.tabs)
    
    def add_tab(self, name: str, content: pn.pane) -> None:
        """
        Add a tab to the tabs panel.
        
        Parameters
        ----------
        name: str
            Name of the tab.
        content: pn.pane
            Content of the tab.
        """
        self.tabs.append((name, content))
    
    def servable(self) -> BootstrapTemplate:
        """
        Serve the layout.
        """
        return self.template.servable()

    def update_metrics_table(self, data: pd.DataFrame) -> None:
        """
        Update metrics table with new data.
        
        Parameters
        ----------
        data: pd.DataFrame
            Data to display in the metrics table.
        """
        self.tabs[1] = (
            "Metrics Table",
            self.widgets.build_metrics_table(data)
            )

import geopandas as gpd

def generate_map(geodata: gpd.GeoDataFrame) -> go.Figure:
    """
    Generate a map of points.

    Parameters
    ----------
    geodata: geopandas.GeoDataFrame
        One-to-One feature mapping with WRES CSV2-compatible column names.
        Required columns include: ['geometry', 'LEFT FEATURE NAME', 
        'LEFT FEATURE DESCRIPTION', 'RIGHT FEATURE NAME', 'LONGITUDE',
        'LATITUDE']
    """
    if "geometry" not in geodata:
        return go.Figure()
    
    # Build map
    fig = go.Figure(go.Scattermap(
        showlegend=False,
        name="",
        lat=geodata["geometry"].y,
        lon=geodata["geometry"].x,
        mode='markers',
        marker=dict(
            size=15,
            color="cyan"
            ),
        selected=dict(
            marker=dict(
                color="magenta"
            )
        ),
        customdata=geodata[[
            "LEFT FEATURE NAME",
            "LEFT FEATURE DESCRIPTION",
            "RIGHT FEATURE NAME"
            ]],
        hovertemplate=
        "LEFT FEATURE DESCRIPTION: %{customdata[1]}<br>"
        "LEFT FEATURE NAME: %{customdata[0]}<br>"
        "RIGHT FEATURE NAME: %{customdata[2]}<br>"
        "LONGITUDE: %{lon}<br>"
        "LATITUDE: %{lat}<br>"
    ))
    fig.update_layout(
        showlegend=False,
        height=720,
        width=1280,
        margin=dict(l=0, r=0, t=0, b=0),
        map=dict(
            style="satellite-streets",
            center={
                "lat": geodata["geometry"].y.mean(),
                "lon": geodata["geometry"].x.mean()
                },
            zoom=2
        ),
        clickmode="event+select",
        modebar=dict(
            remove=["lasso", "select"]
        ),
        dragmode="zoom"
    )
    return fig

def generate_metrics_plot(
        data: pd.DataFrame,
        left_feature_name: str,
        selected_metric: str
    ) -> go.Figure:
    """
    Generate a metrics plot.

    Parameters
    ----------
    data: pd.DataFrame
        Data containing metrics information.
    left_feature_name: str
        Name of the left feature to filter the data.
    selected_metric: str
        Name of the metric to plot.

    Returns
    -------
    go.Figure
        Plotly figure object containing the metrics plot.
    """
    if "LEFT FEATURE NAME" not in data:
        return go.Figure()
    if "METRIC NAME" not in data:
        return go.Figure()

    # Subset data for the selected feature and metric
    df = data[data["LEFT FEATURE NAME"] == left_feature_name]
    df = df[df["METRIC NAME"] == selected_metric]

    fig = go.Figure()
    
    for period, d in df.groupby("EVALUATION PERIOD", observed=True):
        xmin = d[d["SAMPLE QUANTILE"].isna()]["LEAD HOURS MIN"].values
        xmax = d[d["SAMPLE QUANTILE"].isna()]["LEAD HOURS MAX"].values
        nom_y = d[d["SAMPLE QUANTILE"].isna()]["STATISTIC"].values
        upper = d[d["SAMPLE QUANTILE"] == 0.975]["STATISTIC"].values
        lower = d[d["SAMPLE QUANTILE"] == 0.025]["STATISTIC"].values
        
        if len(nom_y) == len(upper) == len(lower):
            error_y = dict(
                type="data",
                array=upper - nom_y,
                arrayminus=nom_y - lower
            )
        else:
            error_y = None
        
        fig.add_trace(go.Bar(
            name=period,
            x=xmin, y=nom_y,
            error_y=error_y,
            legendgroup="bar_plots",
            legendgrouptitle_text="Evaluation Period"
        ))
    
    # Determine ticks
    xmin = sorted(data["LEAD HOURS MIN"].unique().tolist())
    xmax = sorted(data["LEAD HOURS MAX"].unique().tolist())
    xticks = [f"{e}-{l}" for e, l in zip(xmin, xmax)]
    
    fig.update_xaxes(title="LEAD HOURS")
    fig.update_yaxes(title=selected_metric)
    fig.update_layout(
        height=720,
        width=1280,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            tickmode="array",
            tickvals=sorted(xmin),
            ticktext=xticks
        )
    )
    return fig

class Dashboard:
    def __init__(self, title: str):
        self.widgets = Widgets()
        self.layout = Layout(title, self.widgets)
        self.data_manager = DataManager()
        self.feature_descriptions = []

        # Callback for loading data
        def load_data(event):
            if not event:
                return
            self.data_manager.load_data(self.widgets.file_selector.value)
            self.layout.update_metrics_table(
                self.data_manager.data
            )
            self.widgets.map_selector.object = generate_map(
                self.data_manager.feature_mapping
            )
            self.update_feature_selectors()
            self.update_metric_selector()
        pn.bind(load_data, self.widgets.load_data_button, watch=True)

        # Link feature selectors
        def update_left(right_value):
            if not right_value:
                return
            idx = self.widgets.right_feature_selector.options.index(right_value)
            self.widgets.left_feature_selector.value = (
                self.widgets.left_feature_selector.options[idx]
                )
            self.widgets.description_pane.object = (
                    "LEFT FEATURE DESCRIPTION<br>" +
                    self.feature_descriptions[idx]
                )
        def update_right(left_value):
            if not left_value:
                return
            idx = self.widgets.left_feature_selector.options.index(left_value)
            self.widgets.right_feature_selector.value = (
                self.widgets.right_feature_selector.options[idx]
                )
            self.widgets.description_pane.object = (
                    "LEFT FEATURE DESCRIPTION<br>" +
                    self.feature_descriptions[idx]
                )
        def update_from_map(event):
            if not event:
                return
            try:
                point = event["points"][0]
                self.widgets.left_feature_selector.value = point["customdata"][0]
                self.widgets.right_feature_selector.value = point["customdata"][2]
                self.widgets.description_pane.object = (
                    "LEFT FEATURE DESCRIPTION<br>" +
                    point["customdata"][1]
                )
            except Exception as ex:
                self.widgets.description_pane.object = (
                    f"Could not determine site selection: {ex}"
                )
        pn.bind(update_from_map, self.widgets.map_selector.param.click_data, watch=True)
        pn.bind(update_left, right_value=self.widgets.right_feature_selector,
                watch=True)
        pn.bind(update_right, left_value=self.widgets.left_feature_selector,
                watch=True)
        
        # Link metric selector to metrics pane
        def update_metrics_plot(event):
            fig = generate_metrics_plot(
                self.data_manager.data,
                self.widgets.left_feature_selector.value,
                self.widgets.selected_metric.value
            )
            self.widgets.metrics_pane.object = fig
        pn.bind(
            update_metrics_plot,
            self.widgets.selected_metric,
            watch=True
        )
        pn.bind(
            update_metrics_plot,
            self.widgets.left_feature_selector,
            watch=True
        )
    
    def update_feature_selectors(self) -> None:
        if "LEFT FEATURE NAME" not in self.data_manager.feature_mapping:
            self.widgets.left_feature_selector.options = []
            self.widgets.right_feature_selector.options = []
            self.feature_descriptions = []
            self.widgets.left_feature_selector.value = None
            self.widgets.right_feature_selector.value = None
            self.widgets.description_pane.object = (
                "LEFT FEATURE DESCRIPTION<br>"
                "No data loaded"
            )
            return
        self.widgets.left_feature_selector.options = (
            self.data_manager.feature_mapping[
                "LEFT FEATURE NAME"].tolist())
        self.widgets.right_feature_selector.options = (
            self.data_manager.feature_mapping[
                "RIGHT FEATURE NAME"].tolist())
        self.feature_descriptions = (
            self.data_manager.feature_mapping[
                "LEFT FEATURE DESCRIPTION"].tolist())
    
    def update_metric_selector(self) -> None:
        if "METRIC NAME" not in self.data_manager.data:
            self.widgets.selected_metric.options = []
            return
        self.widgets.selected_metric.options = (
            self.data_manager.data["METRIC NAME"].unique().tolist())
    
    def servable(self) -> BootstrapTemplate:
        """
        Serve the dashboard.
        """
        return self.layout.servable()

@click.command()
def run() -> None:
    """
    Visualize and explore metrics output from WRES CSV2 formatted output.

    Run "wres-explorer" from the command-line, ctrl+c to stop the server.:
    """
    # Start interface
    pn.serve(Dashboard("WRES CSV Explorer").servable())

if __name__ == "__main__":
    run()

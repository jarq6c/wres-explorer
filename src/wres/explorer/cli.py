import click
import panel as pn
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from .data import load_dataframes

pn.extension("tabulator")
pn.extension("plotly")

class DataManager:
    """
    Handle the data loading and processing.

    Attributes
    ----------
    data: pd.DataFrame
        Data loaded from the CSV files.
    feature_mapping: pd.DataFrame
        Mapping of features to their descriptions and geometries.
    """
    def __init__(self):
        self.data: pd.DataFrame = None
        self.feature_mapping: pd.DataFrame = None
    
    def load_data(self, filepaths: list[str]):
        if len(filepaths) == 0:
            self.data = pd.DataFrame({"message": ["no data loaded"]})
        else:
            try:
                self.data = load_dataframes(filepaths)
                self.feature_mapping = self.data[[
                    "LEFT FEATURE NAME",
                    "LEFT FEATURE DESCRIPTION",
                    "RIGHT FEATURE NAME",
                    "LEFT FEATURE WKT"
                    ]].drop_duplicates().astype(str)
                self.feature_mapping["geometry"] = gpd.GeoSeries.from_wkt(
                    self.feature_mapping["LEFT FEATURE WKT"])
                self.feature_mapping = gpd.GeoDataFrame(self.feature_mapping)
            except pd.errors.ParserError:
                self.data = pd.DataFrame({"message": ["parsing error"]})
            except KeyError:
                self.data = pd.DataFrame({"message": ["column error"]})

class Dashboard:
    """
    Dashboard for displaying WRES CSV data.
    
    Attributes
    ----------
    title: str
        Title of the dashboard.
    data_manager: DataManager
        Instance of DataManager to handle data loading.
    file_selector: pn.widgets.FileSelector
        File selector widget for selecting CSV files.
    load_data_button: pn.widgets.Button
        Button to load/reload data.
    tabs: pn.Tabs
        Tabs for displaying different sections of the dashboard.
    left_feature_selector: pn.widgets.AutocompleteInput
        Autocomplete input for selecting left feature.
    right_feature_selector: pn.widgets.AutocompleteInput
        Autocomplete input for selecting right feature.
    map_selector: pn.pane.Plotly
        Pane for displaying the map of features.
    description_pane: pn.pane.Markdown
        Pane for displaying feature descriptions.
    feature_descriptions: list
        List of feature descriptions.
    """
    def __init__(self, title: str):
        self.title = title
        self.data_manager = DataManager()
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
        self.tabs = pn.Tabs()
        self.add_tab(
            "File Selector",
            pn.Column(self.file_selector, self.load_data_button)
            )
        
        # Link file selector and data manager
        def update_metrics_data(event):
            self.data_manager.load_data(self.file_selector.value)
            self.update_metrics_table(
                self.data_manager.data, self.data_manager.feature_mapping)
        pn.bind(update_metrics_data, self.load_data_button, watch=True)
        
        # Metrics table
        metrics_table = pn.widgets.Tabulator(
            pd.DataFrame({"message": ["no data loaded"]}),
            show_index=False,
            disabled=True,
            width=1280,
            height=720
        )
        self.add_tab(
            "Metrics Table",
            metrics_table
        )

        # Feature selectors
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
        self.map_selector = pn.pane.Plotly()
        self.description_pane = pn.pane.Markdown(
            "LEFT FEATURE DESCRIPTION\n"
        )
        self.feature_descriptions: list = []

        # Link feature selectors
        def update_left(right_value) -> None:
            if not right_value:
                return
            idx = self.right_feature_selector.options.index(right_value)
            self.left_feature_selector.value = (
                self.left_feature_selector.options[idx]
                )
            self.description_pane.object = (
                    "LEFT FEATURE DESCRIPTION<br>" +
                    self.feature_descriptions[idx]
                )
        def update_right(left_value) -> None:
            if not left_value:
                return
            idx = self.left_feature_selector.options.index(left_value)
            self.right_feature_selector.value = (
                self.right_feature_selector.options[idx]
                )
            self.description_pane.object = (
                    "LEFT FEATURE DESCRIPTION<br>" +
                    self.feature_descriptions[idx]
                )
        pn.bind(update_left, right_value=self.right_feature_selector,
                watch=True)
        pn.bind(update_right, left_value=self.left_feature_selector,
                watch=True)
        
        # Link map to feature selectors
        def update_map(event):
            if not event:
                return
            try:
                point = event["points"][0]
                self.left_feature_selector.value = point["customdata"][0]
                self.right_feature_selector.value = point["customdata"][2]
                self.description_pane.object = (
                    "LEFT FEATURE DESCRIPTION<br>" +
                    point["customdata"][1]
                )
            except Exception as ex:
                self.description_pane.object = (
                    f"Could not determine site selection: {ex}"
                )
        pn.bind(update_map, self.map_selector.param.click_data, watch=True)

        # Layout feature selectors
        self.add_tab(
            "Feature Selector",
            pn.Row(
                pn.Column(
                    self.left_feature_selector,
                    self.right_feature_selector,
                    self.description_pane
                    ),
                self.map_selector
            )
        )

        # Metrics plots
        self.selected_metric = pn.widgets.Select(
            name="Select Metric",
            options=[]
        )
        self.metrics_pane = pn.pane.Plotly()

        # Link metric selector to metrics pane
        def update_metrics_plot(event):
            if not self.selected_metric.value:
                return
            if not self.left_feature_selector.value:
                return
            # Subset
            fname = self.left_feature_selector.value
            mname = self.selected_metric.value
            df = self.data_manager.data
            df = df[df["LEFT FEATURE NAME"] == fname]
            df = df[df["METRIC NAME"] == mname]

            # Plot
            fig = go.Figure()
            for period, d in df.groupby("EVALUATION PERIOD", observed=True):
                nom_x = d[d["SAMPLE QUANTILE"].isna()]["LEAD HOURS"].values
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
                    x=nom_x, y=nom_y,
                    error_y=error_y,
                    legendgroup="bar_plots",
                    legendgrouptitle_text="Bar Plots"
                ))
            fig.update_xaxes(title="LEAD HOURS")
            fig.update_yaxes(title=mname)
            fig.update_layout(
                height=720,
                width=1280,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            self.metrics_pane.object = fig
        pn.bind(
            update_metrics_plot,
            self.selected_metric,
            watch=True
        )
        pn.bind(
            update_metrics_plot,
            self.left_feature_selector,
            watch=True
        )

        # Layout metrics plots
        self.add_tab(
            "Metrics Plots",
            pn.Row(
                pn.Column(
                    self.description_pane,
                    self.selected_metric
                ),
                self.metrics_pane
            )
        )
    
    def update_metrics_table(
            self,
            data: pd.DataFrame,
            feature_mapping: pd.DataFrame
            ) -> None:
        """
        Update metrics table.
        
        Parameters
        ----------
        data: pd.DataFrame
            Data to display in the table.
        feature_mapping: pd.DataFrame
            Feature mapping data.
        """
        metric_filters = {
            'LEFT FEATURE NAME': {
                'type': 'input',
                'func': 'like',
                'placeholder':
                'Enter feature name'
                },
            'RIGHT FEATURE NAME': {
                'type': 'input',
                'func': 'like',
                'placeholder': 'Enter feature name'
                },
            'LEFT FEATURE DESCRIPTION': {
                'type': 'input',
                'func': 'like',
                'placeholder': 'Enter description'
                },
            'METRIC NAME': {
                'type': 'input',
                'func': 'like',
                'placeholder': 'Enter metric name'
                }
        }
        self.tabs[1] = ("Metrics Table", pn.widgets.Tabulator(
            data,
            show_index=False,
            disabled=True,
            width=1280,
            height=720,
            header_filters=metric_filters
        ))
        
        # Check for data
        if "METRIC NAME" not in self.data_manager.data:
            self.left_feature_selector.options = []
            self.right_feature_selector.options = []
            self.feature_descriptions = []
            self.map_selector.object = go.Figure()
            self.description_pane.object = (
                "LEFT FEATURE DESCRIPTION<br>"
                "No data loaded"
            )
            self.selected_metric.options = []
            self.metrics_pane.object = go.Figure()
            self.left_feature_selector.value = None
            self.right_feature_selector.value = None
            self.selected_metric.value = None
            return
        
        # Update feature selectors
        self.left_feature_selector.options = feature_mapping[
            "LEFT FEATURE NAME"].tolist()
        self.right_feature_selector.options = feature_mapping[
            "RIGHT FEATURE NAME"].tolist()
        self.feature_descriptions = feature_mapping[
            "LEFT FEATURE DESCRIPTION"].tolist()
        
        # Build site map
        fig = go.Figure(go.Scattermap(
            showlegend=False,
            name="",
            lat=feature_mapping["geometry"].y,
            lon=feature_mapping["geometry"].x,
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
            customdata=feature_mapping[[
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
                    "lat": feature_mapping["geometry"].y.mean(),
                    "lon": feature_mapping["geometry"].x.mean()
                    },
                zoom=2
            ),
            clickmode="event+select",
            modebar=dict(
                remove=["lasso", "select"]
            )
        )
        self.map_selector.object = fig

        # Update metrics selection
        self.selected_metric.options = (
            self.data_manager.data["METRIC NAME"].unique().tolist())
    
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
    
    def serve(self) -> None:
        """
        Serve the dashboard.
        
        Returns
        -------
        None
        """
        template = pn.template.BootstrapTemplate(title=self.title)
        template.main.append(self.tabs)
        pn.serve(template.servable()) 

@click.command()
def run() -> None:
    """
    Visualize and explore metrics output from WRES CSV2 formatted output.

    Run "wres-explorer" from the command-line, ctrl+c to stop the server.:
    """
    # Start interface
    Dashboard("WRES CSV Explorer").serve()

if __name__ == "__main__":
    run()

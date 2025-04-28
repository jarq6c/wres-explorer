"""Widgets for the dashboard."""
import panel as pn
import pandas as pd

pn.extension("tabulator")

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
    
    Methods
    -------
    build_metrics_table
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
    def build_metrics_table(data: pd.DataFrame) -> pn.widgets.Tabulator:
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

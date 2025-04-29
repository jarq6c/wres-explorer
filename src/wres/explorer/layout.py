"""Layout widgets for the dashboard."""
from typing import Protocol
import pandas as pd
import panel as pn
from panel.template import BootstrapTemplate
from .widgets import Widgets

class TableBuilder(Protocol):
    """
    Build a metrics table from the given data.
    
    Parameters
    ----------
    data: pd.DataFrame
        Data to display in the metrics table.
    
    Returns
    -------
    pn.widgets.Tabulator
        A Tabulator widget displaying the metrics table.
    """
    @staticmethod
    def __call__(data: pd.DataFrame) -> pn.widgets.Tabulator:
        ...

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
        self.add_tab(
            "Pairs Plots",
            self.widgets.pairs_pane
        )
        self.add_tab(
            "Metrics Table",
            self.widgets.build_table(
                pd.DataFrame({"message": ["no data loaded"]})
        ))
        self.add_tab(
            "Pairs Table",
            self.widgets.build_table(
                pd.DataFrame({"message": ["no data loaded"]})
        ))
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

    def update_metrics_table(
            self,
            data: pd.DataFrame,
            table_builder: TableBuilder,
            left_feature_name: str | None = None,
            metric_name: str | None = None
            ) -> None:
        """
        Update metrics table with new data.
        
        Parameters
        ----------
        data: pd.DataFrame
            Data to display in the metrics table.
        """
        df = data
        if left_feature_name is not None:
            df = df[df["LEFT FEATURE NAME"] == left_feature_name]
        if metric_name is not None:
            df = df[df["METRIC NAME"] == metric_name]

        self.tabs[4] = (
            "Metrics Table",
            table_builder(df)
            )

    def update_pairs_table(
            self,
            data: pd.DataFrame,
            table_builder: TableBuilder,
            feature_name: str | None = None
            ) -> None:
        """
        Update pairs table with new data.
        
        Parameters
        ----------
        data: pd.DataFrame
            Data to display in the pairs table.
        """
        if feature_name is not None:
            df = data[data["FEATURE NAME"] == feature_name]
        else:
            df = data

        self.tabs[5] = (
            "Pairs Table",
            table_builder(df)
            )

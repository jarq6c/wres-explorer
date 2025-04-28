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

    def update_metrics_table(
            self,
            data: pd.DataFrame,
            table_builder: TableBuilder) -> None:
        """
        Update metrics table with new data.
        
        Parameters
        ----------
        data: pd.DataFrame
            Data to display in the metrics table.
        """
        self.tabs[1] = (
            "Metrics Table",
            table_builder(data)
            )

"""Callbacks for dashboard."""
import panel as pn
from .data import DataManager
from .layout import Layout
from .widgets import Widgets
from .plots import generate_map, generate_metrics_plot

class Callbacks:
    """Class to handle callbacks for the dashboard.
    
    Attributes
    ----------
    data_manager : DataManager
        Instance of DataManager to handle data loading and processing.
    layout : Layout
        Instance of Layout to manage the layout of the dashboard.
    widgets : Widgets
        Instance of Widgets to manage the widgets in the dashboard.
    """
    def __init__(
            self,
            data_manager: DataManager,
            layout: Layout,
            widgets: Widgets
        ) -> None:
        self.data_manager = data_manager
        self.layout = layout
        self.widgets = widgets
        self.feature_descriptions = []

        # Callback for loading data
        def load_data(event):
            if not event:
                return
            self.data_manager.load_data(self.widgets.file_selector.value)
            self.layout.update_metrics_table(
                self.data_manager.data,
                self.widgets.build_metrics_table
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

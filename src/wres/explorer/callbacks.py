"""Callbacks for dashboard."""
import panel as pn
from .data import DataManager
from .layout import Layout
from .widgets import Widgets
from .plots import generate_map, generate_metrics_plot, generate_pairs_plot
from .plots import invert_color
from .images import ImageManager

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
    feature_descriptions : list
        List of feature descriptions for the left feature selector.
    """
    def __init__(
            self,
            data_manager: DataManager,
            layout: Layout,
            widgets: Widgets,
            image_manager: ImageManager
        ) -> None:
        self.data_manager = data_manager
        self.layout = layout
        self.widgets = widgets
        self.image_manager = image_manager
        self.feature_descriptions = []
        self.curve_number: int | None = None
        self.curve_width: int | None = None
        self.curve_color: str | None = None

        # Navigation
        def update_button_style(active_tab):
            if active_tab == 0:
                self.widgets.next_tab_button.button_style = "solid"
                self.widgets.back_tab_button.button_style = "outline"
            elif active_tab == (len(self.layout.tabs)-1):
                self.widgets.next_tab_button.button_style = "outline"
                self.widgets.back_tab_button.button_style = "solid"
            else:
                self.widgets.next_tab_button.button_style = "solid"
                self.widgets.back_tab_button.button_style = "solid"
        def navigate_forward(event):
            if self.layout.tabs.active == (len(self.layout.tabs)-1):
                return
            self.layout.tabs.active += 1
        pn.bind(navigate_forward, self.widgets.next_tab_button, watch=True)
        def navigate_back(event):
            if self.layout.tabs.active == 0:
                return
            self.layout.tabs.active -= 1
        pn.bind(navigate_back, self.widgets.back_tab_button, watch=True)
        pn.bind(update_button_style, self.layout.tabs.param.active, watch=True)

        # Callback for loading data
        def load_data(event):
            if not event:
                return
            self.data_manager.load_data(self.widgets.file_selector.value)
            self.layout.update_metrics_table(
                self.data_manager.data,
                self.widgets.build_table
            )
            self.layout.update_pairs_table(
                self.data_manager.pairs,
                self.widgets.build_table
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
            feature = self.data_manager.feature_mapping.iloc[idx]
            scatter = self.widgets.map_selector.object.data[0]
            scatter.lon = [feature["geometry"].x]
            scatter.lat = [feature["geometry"].y]
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
        
        # Link feature selector to pairs pane
        def update_pairs_plot(event):
            fig = generate_pairs_plot(
                self.data_manager.pairs,
                self.widgets.left_feature_selector.value
            )
            self.widgets.pairs_pane.object = fig
        def highlight_pairs(event):
            if not event:
                return
            if event["points"][0]["curveNumber"] == self.curve_number:
                  return
            if self.curve_number is not None:
                trace = self.widgets.pairs_pane.object.data[self.curve_number]
                trace["line"]["color"] = self.curve_color
                trace["line"]["width"] = self.curve_width
            self.curve_number = event["points"][0]["curveNumber"]
            trace = self.widgets.pairs_pane.object.data[self.curve_number]
            if "lines" not in trace["mode"]:
                return
            self.curve_color = trace["line"]["color"]
            self.curve_width = trace["line"]["width"]
            trace["line"]["color"] = invert_color(self.curve_color)
            trace["line"]["width"] = self.curve_width + 4
        pn.bind(
            update_pairs_plot,
            self.widgets.left_feature_selector,
            watch=True
        )
        pn.bind(highlight_pairs,
                self.widgets.pairs_pane.param.click_data, watch=True)
        
        # Callback for loading images
        def load_images(event):
            if not event:
                return
            self.image_manager.set_filepaths(self.widgets.image_selector.value)
            if not self.image_manager.filepaths:
                self.layout.update_images([])
                self.layout.clear_image_card()
                return
            self.layout.update_images(self.image_manager.images.keys())
        pn.bind(load_images, self.widgets.load_images_button, watch=True)
        def update_image(event):
            if not event:
                return
            if event not in self.image_manager.images:
                self.layout.clear_image_card()
                return
            image = self.image_manager.images[event]
            self.layout.update_image_card(image)
        pn.bind(update_image, self.widgets.image_player, watch=True)
    
    def update_feature_selectors(self) -> None:
        """Update the feature selector options based on loaded data."""
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
        """Update the metric selector options based on loaded data."""
        if "METRIC NAME" not in self.data_manager.data:
            self.widgets.selected_metric.options = []
            return
        self.widgets.selected_metric.options = (
            self.data_manager.data["METRIC NAME"].unique().tolist())

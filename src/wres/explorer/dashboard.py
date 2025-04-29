"""Combine all the components of the dashboard into a single app."""
import panel as pn
from .data import DataManager
from .widgets import Widgets
from .layout import Layout
from .callbacks import Callbacks

class Dashboard:
    def __init__(self, title: str):
        self.data_manager = DataManager()
        self.widgets = Widgets()
        self.layout = Layout(title, self.widgets)
        self.callbacks = Callbacks(
            data_manager=self.data_manager,
            layout=self.layout,
            widgets=self.widgets
        )

    def serve(self):
        """
        Serve the dashboard.
        """
        pn.serve(self.layout.servable())

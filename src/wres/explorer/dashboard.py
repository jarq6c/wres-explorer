"""Combine all the components of the dashboard into a single app."""
import panel as pn
from panel.template import BootstrapTemplate
from .data import DataManager
from .widgets import Widgets
from .layout import Layout
from .callbacks import Callbacks
from .images import ImageManager

class Dashboard:
    """Dashboard class to combine all components into a single app.
    
    Attributes
    ----------
    title : str
        The title of the dashboard.
    data_manager : DataManager
        Instance of DataManager to handle data operations.
    widgets : Widgets
        Instance of Widgets to manage dashboard widgets.
    layout : Layout
        Instance of Layout to manage the dashboard layout.
    callbacks : Callbacks
        Instance of Callbacks to handle interactions and updates.
    """
    def __init__(self, title: str):
        self.data_manager = DataManager()
        self.widgets = Widgets()
        self.layout = Layout(title, self.widgets)
        self.image_manager = ImageManager()
        self.callbacks = Callbacks(
            data_manager=self.data_manager,
            layout=self.layout,
            widgets=self.widgets,
            image_manager=self.image_manager
        )

    def serve(self) -> BootstrapTemplate:
        """
        Serve the dashboard.
        """
        return self.layout.servable()

def dashboard_factory() -> Dashboard:
    """Factory function to create a Dashboard instance."""
    return Dashboard("WRES Explorer").serve()

def serve_dashboard() -> None:
    """Serve the dashboard."""
    pn.serve(dashboard_factory)

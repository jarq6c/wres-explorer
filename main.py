import panel as pn
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
from src.wres.explorer.data import load_dataframes

pn.extension("tabulator")
pn.extension("plotly")

class DataManager:
    """
    Handle loading and managing of data.
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

class Components:
    """
    Handle the components of the dashboard.

    Attributes
    ----------
    file_selector: pn.widgets.FileSelector
        File selector widget for selecting data files.
    load_data_button: pn.widgets.Button
        Button for loading data.
    feature_description: pn.pane.Markdown
        Markdown pane for displaying feature descriptions.
    tabs: pn.Tabs
        Tabs for organizing the dashboard content.
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
        self.feature_description = pn.pane.Markdown(
            "LEFT FEATURE DESCRIPTION: \n"
        )
        self.tabs = pn.Tabs()
        self.add_tab(
            "File Selector",
            pn.Column(self.file_selector, self.load_data_button)
            )
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
            "LEFT FEATURE DESCRIPTION: \n"
        )
        self.feature_descriptions: list = []

        # Link feature selectors
        def update_left(right_value) -> None:
            if right_value is None:
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
        
        Returns
        -------
        pn.widgets.Tabulator
            Tabulator widget displaying the data.
        """
        self.tabs[1] = ("Metrics Table", pn.widgets.Tabulator(
            data,
            show_index=False,
            disabled=True,
            width=1280,
            height=720
        ))
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
            )
        )
        self.map_selector.object = fig
    
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

def serve_dashboard(title: str) -> None:
    """
    Serve the dashboard.
    
    Returns
    -------
    None
    """
    # Initialize components
    components = Components()
    
    # Initialize data manager
    data_manager = DataManager()

    # Load data
    def update_data(event):
        data_manager.load_data(components.file_selector.value)
        components.update_metrics_table(
            data_manager.data, data_manager.feature_mapping)
    pn.bind(update_data, components.load_data_button, watch=True)

    # Serve the dashboard
    dashboard = pn.template.BootstrapTemplate(title=title)
    dashboard.main.append(components.tabs)
    pn.serve(dashboard.servable())

def run():
    # Tabs
    tabs = pn.Tabs()

    # File selector tab
    files = pn.widgets.FileSelector(
        directory="./",
        file_pattern="*.csv.gz",
        only_files=True,
        value=[]
    )
    load_data = pn.widgets.Button(
        name="Load/Reload Data",
        button_type="primary"
        )
    tabs.append(("File Selector", pn.Column(files, load_data)))

    # Metrics table tab
    data: pd.DataFrame = None
    feature_map: pd.DataFrame = None
    feature_description = pn.pane.Markdown(
        "LEFT FEATURE DESCRIPTION: \n"
    )
    def update_metrics_table(event):
        nonlocal data
        nonlocal feature_map
        if not event:
            data = pd.DataFrame({"message": ["no data loaded"]})
        if len(files.value) == 0:
            data = pd.DataFrame({"message": ["no data loaded"]})
        else:
            try:
                data = load_dataframes(files.value)
                feature_map = data[[
                    "LEFT FEATURE NAME",
                    "LEFT FEATURE DESCRIPTION",
                    "RIGHT FEATURE NAME",
                    "LEFT FEATURE WKT"
                    ]].drop_duplicates().astype(str)
                feature_map["geometry"] = gpd.GeoSeries.from_wkt(
                    feature_map["LEFT FEATURE WKT"])
                feature_map = gpd.GeoDataFrame(feature_map)
                feature_description.object = "LEFT FEATURE DESCRIPTION: \n"
            except pd.errors.ParserError:
                data = pd.DataFrame({"message": ["parsing error"]})
            except KeyError:
                data = pd.DataFrame({"message": ["column error"]})

        return pn.widgets.Tabulator(
            data,
            show_index=False,
            disabled=True,
            width=1280,
            height=720
        )
    tabs.append(("Metrics Table", pn.bind(update_metrics_table, load_data)))

    # Site selector tab
    left_feature_name: str = None
    right_feature_name: str = None
    def update_site_selector(event):
        nonlocal feature_map
        nonlocal left_feature_name
        nonlocal right_feature_name
        if not event:
            return update_metrics_table(event)
        if len(files.value) == 0:
            return update_metrics_table(event)
        if feature_map is None:
            return update_metrics_table(event)
        
        # Build interface
        left_feature = pn.widgets.AutocompleteInput(
            name="LEFT FEATURE NAME",
            options=feature_map["LEFT FEATURE NAME"].tolist(),
            search_strategy="includes",
            placeholder="Select LEFT FEATURE NAME"
        )
        right_feature = pn.widgets.AutocompleteInput(
            name="RIGHT FEATURE NAME",
            options=feature_map["RIGHT FEATURE NAME"].tolist(),
            search_strategy="includes",
            placeholder="Select RIGHT FEATURE NAME"
        )
        
        # Build site map
        fig = go.Figure(go.Scattermap(
            showlegend=False,
            name="",
            lat=feature_map["geometry"].y,
            lon=feature_map["geometry"].x,
            mode='markers',
            marker=dict(
                size=15,
                color="cyan"
                ),
            customdata=feature_map[[
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
                    "lat": feature_map["geometry"].y.mean(),
                    "lon": feature_map["geometry"].x.mean()
                    },
                zoom=2
            )
        )
        site_map = pn.pane.Plotly(fig)

        # Link map to features
        def update_map(event):
            nonlocal left_feature_name
            nonlocal right_feature_name
            nonlocal right_feature
            nonlocal left_feature
            if not event:
                return
            try:
                point = event["points"][0]
                left_feature_name = point["customdata"][0]
                left_feature.value = point["customdata"][0]
                right_feature_name = point["customdata"][2]
                right_feature.value = point["customdata"][2]
                feature_description.object = (
                    "LEFT FEATURE DESCRIPTION<br>" +
                    point["customdata"][1]
                )
            except Exception as ex:
                feature_description.object = (
                    f"Could not determine site selection: {ex}"
                )
        pn.bind(update_map, site_map.param.click_data, watch=True)

        # Link left and right feature
        def update_right_feature(left):
            nonlocal left_feature_name
            nonlocal right_feature_name
            nonlocal right_feature
            df = feature_map[feature_map["LEFT FEATURE NAME"] == left]
            if df.empty:
                return
            right_feature.value = df["RIGHT FEATURE NAME"].iloc[0]
            right_feature_name = df["RIGHT FEATURE NAME"].iloc[0]
            left_feature_name = df["LEFT FEATURE NAME"].iloc[0]
            feature_description.object = (
                "LEFT FEATURE DESCRIPTION<br>" +
                df["LEFT FEATURE DESCRIPTION"].iloc[0]
            )
        pn.bind(update_right_feature, left=left_feature, watch=True)

        # Link right and left feature
        def update_left_feature(right):
            nonlocal left_feature_name
            nonlocal right_feature_name
            nonlocal left_feature
            df = feature_map[feature_map["RIGHT FEATURE NAME"] == right]
            if df.empty:
                return
            left_feature.value = df["LEFT FEATURE NAME"].iloc[0]
            left_feature_name = df["LEFT FEATURE NAME"].iloc[0]
            right_feature_name = df["RIGHT FEATURE NAME"].iloc[0]
            feature_description.object = (
                "LEFT FEATURE DESCRIPTION<br>" +
                df["LEFT FEATURE DESCRIPTION"].iloc[0]
            )
        pn.bind(update_left_feature, right=right_feature, watch=True)
        
        # Layout
        return pn.Row(pn.Column(
            left_feature,
            right_feature,
            feature_description
        ), site_map)
    tabs.append(("Site Selector", pn.bind(update_site_selector, load_data)))

    # Build and serve the dashboard
    dashboard = pn.template.BootstrapTemplate(title="WRES Explorer")
    dashboard.main.append(tabs)
    pn.serve(dashboard.servable())

if __name__ == "__main__":
    serve_dashboard("WRES CSV Viewer")

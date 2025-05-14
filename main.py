import polars as pl
import polars.datatypes as pldt
import numpy as np

from dataclasses import dataclass
from datetime import datetime
import plotly.graph_objects as go
import colorcet as cc
import panel as pn
from param.parameterized import Parameter
import geopandas as gpd

DTYPE_MAPPING: dict[str, pl.DataType] = {
    "LEFT FEATURE NAME": pldt.String,
    "LEFT FEATURE WKT": pldt.String,
    "LEFT FEATURE DESCRIPTION": pldt.String,
    "RIGHT FEATURE NAME": pldt.String,
    "LATEST ISSUED TIME INCLUSIVE": pldt.Datetime,
    "EARLIEST ISSUED TIME EXCLUSIVE": pldt.Datetime,
    "EARLIEST LEAD DURATION EXCLUSIVE": pldt.String,
    "LATEST LEAD DURATION INCLUSIVE": pldt.String,
    "METRIC NAME": pldt.Categorical,
    "SAMPLE QUANTILE": pldt.Float32,
    "STATISTIC": pldt.Float32
}
"""Mapping from WRES standard column names to polars datatypes."""

@dataclass
class DataManager:
    """Dataclass for managing and retrieving WRES evaluation output."""
    file_list: list[str] | None = None
    dtype_mapping: dict[str, pl.DataType] | None = None

    def __post_init__(self):
        if self.dtype_mapping is None:
            self.dtype_mapping = DTYPE_MAPPING

    def load_dataframe(self) -> pl.DataFrame:
        """Lazily scan input files and return dataframe."""
        return pl.scan_csv(
            self.file_list,
            schema_overrides=self.dtype_mapping
            ).select(list(self.dtype_mapping.keys())
            ).with_columns(
                (pl.col("LATEST ISSUED TIME INCLUSIVE") -
                pl.col("EARLIEST ISSUED TIME EXCLUSIVE")
                ).alias("EVALUATION PERIOD"),
                pl.col("EARLIEST LEAD DURATION EXCLUSIVE"
                    ).str.extract("(\\d+)").alias(
                        "EARLIEST LEAD TIME").cast(pldt.Int32),
                pl.col("LATEST LEAD DURATION INCLUSIVE"
                    ).str.extract("(\\d+)").alias(
                        "LATEST LEAD TIME").cast(pldt.Int32)
            )
    
    def load_feature_mapping(self) -> pl.DataFrame:
        return self.load_dataframe().select(
            pl.col("LEFT FEATURE DESCRIPTION"),
            pl.col("LEFT FEATURE NAME"),
            pl.col("RIGHT FEATURE NAME"),
            pl.col("LEFT FEATURE WKT")
        ).unique()
    
    def load_metrics(
        self,
        *filters,
        select: list[str] | None = None
        ) -> pl.DataFrame:
        if select is None:
            return self.load_dataframe(
                ).filter(
                    *filters
                )
        return self.load_dataframe(
            ).filter(
                *filters
            ).select(select)
    
    @property
    def geometry(self) -> gpd.GeoSeries:
        return gpd.GeoSeries.from_wkt(
            self.load_feature_mapping().select(
                pl.col("LEFT FEATURE WKT")
            ).collect().to_pandas()["LEFT FEATURE WKT"]
        )
    
    @property
    def start_date(self) -> datetime:
        return self.load_dataframe().select(
            pl.col("EARLIEST ISSUED TIME EXCLUSIVE")
        ).min().collect().item(row=0, column=0)
    
    @property
    def end_date(self) -> datetime:
        return self.load_dataframe().select(
            pl.col("LATEST ISSUED TIME INCLUSIVE")
        ).max().collect().item(row=0, column=0)

data_manager = DataManager(["data/ABRFC.evaluation.csv.gz"])

print(data_manager.load_metrics(
    (pl.col("EARLIEST LEAD TIME") == 0),
    (pl.col("SAMPLE QUANTILE").is_null()),
    (pl.col("EVALUATION PERIOD") == pl.duration(days=90)),
    (pl.col("METRIC NAME") == "BIAS FRACTION"),
    select=["LEFT FEATURE NAME", "STATISTIC"]
    ).collect())
# TODO setup SiteSelector to work with functions that retrieve data
quit()

@dataclass
class SiteSelector:
    """
    A clickable mapping interface to display evaluation statistics on a
    map and select points for more detailed inspection.
    """
    model_name: str
    start_date: datetime
    end_date: datetime
    metric_labels: list[str]
    usgs_site_codes: list[str]
    nwm_feature_ids: list[str]
    site_descriptions: list[str]
    latitudes: list[float]
    longitudes: list[float]
    statistics: list[list[float]]
    _freeze_updates: bool = False
    _layout: go.Layout | None = None
    _map_pane: pn.pane.Plotly | None = None
    _left_feature_selector: pn.widgets.AutocompleteInput | None = None

    def generate(self) -> pn.Row:
        # Selection highlight marker
        selected_marker = go.Scattermap(
            showlegend=False,
            name="",
            lat=self.latitudes[:1],
            lon=self.longitudes[:1],
            mode="markers",
            marker=dict(
                size=1,
                color="magenta"
                ),
            selected=dict(
                marker=dict(
                    color="magenta"
                )
            ),
        )

        # Main map
        scatter_map = go.Scattermap(
            showlegend=False,
            name="",
            lat=self.latitudes,
            lon=self.longitudes,
            mode="markers",
            marker=dict(
                size=15,
                color=self.statistics[0],
                colorscale=cc.gouldian,
                colorbar=dict(title=dict(
                    text=self.metric_labels[0], side="right")),
                cmin=-1.0,
                cmax=1.0
                ),
            customdata=np.column_stack((
                self.site_descriptions,
                self.usgs_site_codes,
                self.nwm_feature_ids
            )),
            hovertemplate=
            "%{customdata[0]}<br>"
            "USGS Site Code: %{customdata[1]}<br>"
            "NWM Feature ID: %{customdata[2]}<br>"
            "Longitude: %{lon}<br>"
            "Latitude: %{lat}<br><br>"
            "Bias Fraction: %{marker.color:.2f}<br>"
        )

        # Layout configuration
        self._layout = go.Layout(
            showlegend=False,
            height=720,
            width=1280,
            margin=dict(l=0, r=0, t=50, b=0),
            map=dict(
                style="satellite-streets",
                center={
                    "lat": np.mean(self.latitudes),
                    "lon": np.mean(self.longitudes)
                    },
                zoom=3
            ),
            clickmode="event",
            modebar=dict(
                remove=["lasso", "select"]
            ),
            dragmode="zoom"
        )

        # Patch for updating map
        self.figure_data = {
            "data": [selected_marker, scatter_map],
            "layout": self._layout
        }

        # Widgets
        self._map_pane = pn.pane.Plotly(self.figure_data)
        self._left_feature_selector = pn.widgets.AutocompleteInput(
            name="USGS Site Code",
            options=self.usgs_site_codes,
            search_strategy="includes",
            placeholder="Enter USGS site code"
        )
        right_feature_selector = pn.widgets.AutocompleteInput(
            name="NWM Feature ID",
            options=self.nwm_feature_ids,
            search_strategy="includes",
            placeholder="Enter NWM feature ID"
        )
        self._selected_metric = pn.widgets.Select(
            name="Metric",
            options=self.metric_labels
        )

        # Build layout elements
        detail_card = pn.Card(
            pn.Column(
                pn.pane.Markdown(
                    f"**Configuration**: {self.model_name}<br>"
                    f"**Start date**: {self.start_date}<br>"
                    f"**End date**: {self.end_date}<br>"
                ),
                self._selected_metric
            ),
            title="Evaluation Details",
            collapsible=False,
            margin=10,
            width=325
        )
        site_card = pn.Card(
            self._left_feature_selector,
            right_feature_selector,
            collapsible=False,
            title="Site Selection",
            margin=10,
            width=325
        )
        map_card = pn.Card(
            self._map_pane,
            collapsible=False,
            title="Site Map",
            margin=10
        )

        def update_selection(event, source: str):
            if self._freeze_updates:
                return
            if source == "click_data":
                point = event["points"][0]
                lon = point["lon"]
                lat = point["lat"]
                self._freeze_updates = True
                self._left_feature_selector.value = point["customdata"][1]
                right_feature_selector.value = point["customdata"][2]
                self._freeze_updates = False
                if "map.center" in self._map_pane.relayout_data:
                    self.update_zoom(
                        self._map_pane.relayout_data["map.center"]["lat"],
                        self._map_pane.relayout_data["map.center"]["lon"],
                        self._map_pane.relayout_data["map.zoom"]
                        )
            elif source == "left_value":
                idx = self.usgs_site_codes.index(event)
                lon = self.longitudes[idx]
                lat = self.latitudes[idx]
                self._freeze_updates = True
                right_feature_selector.value = self.nwm_feature_ids[idx]
                self._freeze_updates = False
                self.update_zoom(lat, lon)
            elif source == "right_value":
                idx = self.nwm_feature_ids.index(event)
                lon = self.longitudes[idx]
                lat = self.latitudes[idx]
                self._freeze_updates = True
                self._left_feature_selector.value = self.usgs_site_codes[idx]
                self._freeze_updates = False
                self.update_zoom(lat, lon)
            selected_marker.update({
                "lat": [lat], "lon": [lon]
            })
            if selected_marker["marker"]["size"] != 25:
                selected_marker["marker"].update({"size": 25})
            self._map_pane.object = self.figure_data
        pn.bind(update_selection,
                self._map_pane.param.click_data, watch=True,
                source="click_data")
        pn.bind(update_selection,
                self._left_feature_selector.param.value, watch=True,
                source="left_value")
        pn.bind(update_selection,
                right_feature_selector.param.value, watch=True,
                source="right_value")

        # Final layout
        return pn.Row(
            pn.Column(detail_card, site_card),
            map_card
        )
    
    def update_zoom(
            self,
            lat: float,
            lon: float,
            zoom: int = 5
            ) -> None:
        if self._layout is None:
            return
        self._layout["map"]["center"].update({
            "lat": lat,
            "lon": lon
        })
        self._layout["map"].update({
            "zoom": zoom
        })
        self._map_pane.relayout_data.update({
            "map.center": {"lat": lat, "lon": lon}})
        self._map_pane.relayout_data.update({"map.zoom": zoom})
    
    @property
    def selected(self) -> Parameter:
        if self._left_feature_selector is None:
            raise RuntimeError("Must run generate before accessing parameter")
        return self._left_feature_selector.param.value

def get_site_selector() -> pn.Row:
    return SiteSelector(
        model_name="NWM Medium Range Deterministic",
        start_date=start_date,
        end_date=end_date,
        metric_labels=["Bias Fraction (0 to 24 hours)"],
        usgs_site_codes=custom_data["LEFT FEATURE NAME"].to_list(),
        nwm_feature_ids=custom_data["RIGHT FEATURE NAME"].to_list(),
        site_descriptions=custom_data["LEFT FEATURE DESCRIPTION"].to_list(),
        latitudes=custom_data["LATITUDE"].to_list(),
        longitudes=custom_data["LONGITUDE"].to_list(),
        statistics=[custom_data["STATISTIC"].to_list()]
    ).generate()

pn.serve(get_site_selector)

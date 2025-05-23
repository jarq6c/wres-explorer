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
    "EARLIEST VALID TIME EXCLUSIVE": pldt.Datetime,
    "LATEST VALID TIME INCLUSIVE": pldt.Datetime,
    "EARLIEST ISSUED TIME EXCLUSIVE": pldt.Datetime,
    "EARLIEST LEAD DURATION EXCLUSIVE": pldt.String,
    "LATEST LEAD DURATION INCLUSIVE": pldt.String,
    "EVENT THRESHOLD NAME": pldt.Categorical,
    "EVENT THRESHOLD LOWER VALUE": pldt.Float32,
    "METRIC NAME": pldt.Categorical,
    "SAMPLE QUANTILE": pldt.Float32,
    "STATISTIC": pldt.Float32
}
"""Mapping from WRES standard column names to polars datatypes."""

@dataclass
class EvaluationCSVManager:
    """
    Dataclass for managing and retrieving WRES evaluation CSV output.

    Attributes
    ----------
    file_list: list[str], required
        List of file paths to evaluation.csv.gz files containg evaluation
        metrics in WRES csv2 format.
    dtype_mapping: dict[str, pl.DataType], optional
        Mapping from column names to polars data types.
    """
    file_list: list[str]
    dtype_mapping: dict[str, pl.DataType] | None = None

    def __post_init__(self):
        if self.dtype_mapping is None:
            self.dtype_mapping = DTYPE_MAPPING

        self._dataframe = pl.scan_csv(
            self.file_list,
            schema_overrides=self.dtype_mapping,
            null_values=[
                "-1000000000-01-01T00:00:00Z",
                "+1000000000-12-31T23:59:59.999999999Z",
                "PT-2562047788015215H-30M-8S",
                "PT2562047788015215H30M7.999999999S"
            ]
            ).select(list(self.dtype_mapping.keys())
            ).with_columns(
                (pl.col("LATEST ISSUED TIME INCLUSIVE") -
                pl.col("EARLIEST ISSUED TIME EXCLUSIVE")
                ).alias("EVALUATION PERIOD"),
                pl.col("EARLIEST LEAD DURATION EXCLUSIVE"
                    ).str.extract("(\\d+)").alias(
                        "EARLIEST LEAD TIME").cast(pldt.Int32).fill_null(0),
                pl.col("LATEST LEAD DURATION INCLUSIVE"
                    ).str.extract("(\\d+)").alias(
                        "LATEST LEAD TIME").cast(pldt.Int32).fill_null(0)
            )
    
    def query(
        self,
        *filters,
        select: list[str] | None = None
        ) -> pl.DataFrame:
        if select is None:
            return self._dataframe.filter(
                    *filters
                )
        return self._dataframe.filter(
                *filters
            ).select(select)
    
    def load_metric_map(
            self,
            metric_name: str,
            earliest_lead_time: int,
            threshold: str | None = None,
            sample_quantile: float = np.nan,
            evaluation_period: pl.Duration | None = None,
            ) -> gpd.GeoDataFrame:
        if threshold is None:
            thold_filter = pl.col("EVENT THRESHOLD NAME").is_null()
        else:
            thold_filter = pl.col("EVENT THRESHOLD NAME") == threshold
        if np.isnan(sample_quantile):
            sq_filter = pl.col("SAMPLE QUANTILE").is_null()
        else:
            sq_filter = pl.col("SAMPLE QUANTILE") == sample_quantile
        if evaluation_period is None:
            evaluation_period = pl.duration(days=90)
        df = self.query(
            (pl.col("EARLIEST LEAD TIME") == earliest_lead_time),
            sq_filter,
            thold_filter,
            (pl.col("EVALUATION PERIOD") == evaluation_period),
            (pl.col("METRIC NAME") == metric_name),
            select=["LEFT FEATURE NAME", "STATISTIC"]
            ).collect().to_pandas().set_index("LEFT FEATURE NAME")
        df["geometry"] = self.geometry
        return gpd.GeoDataFrame(df)
    
    def metric_range(self, metric_name: str) -> tuple[float, float]:
        df = self.query(
            (pl.col("METRIC NAME") == metric_name),
            select=["STATISTIC"]
            )
        return (df.min().collect().item(row=0, column=0),
            df.max().collect().item(row=0, column=0))

    @property
    def dataframe(self) -> pl.LazyFrame:
        return self._dataframe
    
    @property
    def feature_mapping(self) -> gpd.GeoDataFrame:
        df = self._dataframe.select(
            pl.col("LEFT FEATURE DESCRIPTION"),
            pl.col("LEFT FEATURE NAME"),
            pl.col("RIGHT FEATURE NAME"),
        ).unique().collect().to_pandas().set_index("LEFT FEATURE NAME")
        df["geometry"] = self.geometry
        return gpd.GeoDataFrame(df)
    
    @property
    def geometry(self) -> gpd.GeoSeries:
        df = self._dataframe.select(
            pl.col("LEFT FEATURE NAME"),
            pl.col("LEFT FEATURE WKT")
        ).unique().collect().to_pandas().set_index("LEFT FEATURE NAME")
        return gpd.GeoSeries.from_wkt(df["LEFT FEATURE WKT"])
    
    @property
    def start_date(self) -> datetime:
        return self._dataframe.select(
            pl.col("EARLIEST VALID TIME EXCLUSIVE")
        ).min().collect().item(row=0, column=0)
    
    @property
    def end_date(self) -> datetime:
        return self._dataframe.select(
            pl.col("LATEST VALID TIME INCLUSIVE")
        ).max().collect().item(row=0, column=0)
    
    @property
    def metric_names(self) -> list[str]:
        return self._dataframe.select(
            "METRIC NAME").unique().collect()["METRIC NAME"].to_list()
    
    @property
    def earliest_lead_times(self) -> list[int]:
        return self._dataframe.select(
            "EARLIEST LEAD TIME").unique(
            ).collect()["EARLIEST LEAD TIME"].to_list()
    
    @property
    def thresholds(self) -> list[str]:
        return self._dataframe.select(
            "EVENT THRESHOLD NAME").unique(
            ).collect()["EVENT THRESHOLD NAME"].to_list()

METRIC_COLORBAR_LIMITS: dict[str, tuple[float, float]] = {
    "BIAS FRACTION": (-1.0, 1.0)
}
"""Mapping from metric names to (cmin, cmax) for colorbar vizualizations."""

@dataclass
class SiteSelector:
    """
    A clickable mapping interface to display evaluation statistics on a
    map and select points for more detailed inspection.
    """
    model_name: str
    evaluation_data: EvaluationCSVManager
    metric_colorbar_limits: dict[str, tuple[float, float]] | None = None

    def __post_init__(self) -> None:
        self._freeze_updates: bool = False
        self._left_feature_selector = None
        self._selected_metric = None
        self._lead_time_slider = None
        if self.metric_colorbar_limits is None:
            self.metric_colorbar_limits = METRIC_COLORBAR_LIMITS

    def generate(self) -> pn.Row:
        # Load features and metric data
        metric_names = self.evaluation_data.metric_names
        lead_times = self.evaluation_data.earliest_lead_times
        thresholds = self.evaluation_data.thresholds
        metric_label = metric_names[0]
        features = self.evaluation_data.feature_mapping.reset_index()
        metrics = self.evaluation_data.load_metric_map(
            metric_name=metric_label,
            earliest_lead_time=lead_times[0],
            threshold=thresholds[0]
        )

        # Selection highlight marker
        selected_marker = go.Scattermap(
            showlegend=False,
            name="",
            lat=features["geometry"].y[:1],
            lon=features["geometry"].x[:1],
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
        self.metric_colorbar_limits.update({
            "SAMPLE SIZE": self.evaluation_data.metric_range("SAMPLE SIZE")
        })
        cmin, cmax = self.metric_colorbar_limits.get(
            metric_label, (None, None))
        scatter_map = go.Scattermap(
            showlegend=False,
            name="",
            lat=features["geometry"].y,
            lon=features["geometry"].x,
            mode="markers",
            marker=dict(
                size=15,
                color=metrics["STATISTIC"],
                colorscale=cc.gouldian,
                colorbar=dict(title=dict(
                    text=metric_label, side="right")),
                cmin=cmin,
                cmax=cmax
                ),
            customdata=features.drop("geometry", axis=1),
            hovertemplate=
            "%{customdata[1]}<br>"
            "USGS Site Code: %{customdata[0]}<br>"
            "NWM Feature ID: %{customdata[2]}<br>"
            "Longitude: %{lon}<br>"
            "Latitude: %{lat}<br><br>"
            f"{metric_label}: " + "%{marker.color:.2f}<br>"
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
                    "lat": features["geometry"].y.mean(),
                    "lon": features["geometry"].x.mean()
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
            options=features["LEFT FEATURE NAME"].to_list(),
            search_strategy="includes",
            placeholder="Enter USGS site code"
        )
        right_feature_selector = pn.widgets.AutocompleteInput(
            name="NWM Feature ID",
            options=features["RIGHT FEATURE NAME"].to_list(),
            search_strategy="includes",
            placeholder="Enter NWM feature ID"
        )
        self._selected_metric = pn.widgets.Select(
            name="Metric",
            options=metric_names
        )
        self._lead_time_slider = pn.widgets.DiscreteSlider(
            name="Earliest Lead Hours",
            options=lead_times,
            value=lead_times[0]
        )
        lead_backward = pn.widgets.Button(name="\u25c0", width=50)
        lead_forward = pn.widgets.Button(name="\u25b6", width=50)

        # Lead time increment
        def update_lead_time_value(click, direction: str):
            if not click:
                return
            current_value = self._lead_time_slider.value
            idx = self._lead_time_slider.options.index(current_value)
            if direction == "forward":
                if idx == len(self._lead_time_slider.options)-1:
                    return
                updated = self._lead_time_slider.options[idx+1]
                self._lead_time_slider.value = updated
            if direction == "backward":
                if idx == 0:
                    return
                updated = self._lead_time_slider.options[idx-1]
                self._lead_time_slider.value = updated
        pn.bind(update_lead_time_value, lead_backward, watch=True,
            direction="backward")
        pn.bind(update_lead_time_value, lead_forward, watch=True,
            direction="forward")

        # Build layout elements
        modal = pn.Modal(
            pn.Row(
                pn.pane.Plotly(),
                pn.pane.Plotly()
                ),
            name="Site Details")
        detail_card = pn.Card(
            pn.Column(
                pn.pane.Markdown(
                    f"**Configuration**: {self.model_name}<br>"
                    f"**Start date**: {self.evaluation_data.start_date}<br>"
                    f"**End date**: {self.evaluation_data.end_date}<br>"
                ),
                self._selected_metric,
                self._lead_time_slider,
                pn.Row(lead_backward, lead_forward)
            ),
            title="Evaluation Details",
            collapsible=False,
            margin=10,
            width=325
        )
        site_card = pn.Card(
            self._left_feature_selector,
            right_feature_selector,
            modal,
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
                self._left_feature_selector.value = point["customdata"][0]
                right_feature_selector.value = point["customdata"][2]
                self._freeze_updates = False
                if "map.center" in self._map_pane.relayout_data:
                    self.update_zoom(
                        self._map_pane.relayout_data["map.center"]["lat"],
                        self._map_pane.relayout_data["map.center"]["lon"],
                        self._map_pane.relayout_data["map.zoom"]
                        )
                modal.toggle()
            elif source == "left_value":
                idx = self._left_feature_selector.options.index(event)
                lon = features.iloc[idx, :]["geometry"].x
                lat = features.iloc[idx, :]["geometry"].y
                self._freeze_updates = True
                right_feature_selector.value = right_feature_selector.options[idx]
                self._freeze_updates = False
                self.update_zoom(lat, lon)
            elif source == "right_value":
                idx = right_feature_selector.options.index(event)
                lon = features.iloc[idx, :]["geometry"].x
                lat = features.iloc[idx, :]["geometry"].y
                self._freeze_updates = True
                self._left_feature_selector.value = self._left_feature_selector.options[idx]
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
        
        def update_metric_scatter(metric_label):
            metrics = self.evaluation_data.load_metric_map(
                metric_name=metric_label,
                earliest_lead_time=0
            )
            cmin, cmax = self.metric_colorbar_limits.get(
                metric_label, (None, None))
            scatter_map.update(dict(
                lat=metrics["geometry"].y,
                lon=metrics["geometry"].x,
                customdata=features.drop("geometry", axis=1),
                hovertemplate=
                "%{customdata[1]}<br>"
                "USGS Site Code: %{customdata[0]}<br>"
                "NWM Feature ID: %{customdata[2]}<br>"
                "Longitude: %{lon}<br>"
                "Latitude: %{lat}<br><br>"
                f"{metric_label}: " + "%{marker.color:.2f}<br>"
            ))
            scatter_map["marker"].update(dict(
                color=metrics["STATISTIC"],
                colorbar=dict(
                    title=dict(
                        text=metric_label,
                        side="right"
                        )
                    ),
                    cmin=cmin,
                    cmax=cmax
            ))
            if "map.center" in self._map_pane.relayout_data:
                self.update_zoom(
                    self._map_pane.relayout_data["map.center"]["lat"],
                    self._map_pane.relayout_data["map.center"]["lon"],
                    self._map_pane.relayout_data["map.zoom"]
                    )
            self._map_pane.object = self.figure_data
        pn.bind(update_metric_scatter, self._selected_metric.param.value,
                watch=True)
        
        def update_lead_time_scatter(lead_time):
            metric_label = self._selected_metric.value
            metrics = self.evaluation_data.load_metric_map(
                metric_name=metric_label,
                earliest_lead_time=lead_time
            )
            scatter_map["marker"].update(dict(
                color=metrics["STATISTIC"]
            ))
            if "map.center" in self._map_pane.relayout_data:
                self.update_zoom(
                    self._map_pane.relayout_data["map.center"]["lat"],
                    self._map_pane.relayout_data["map.center"]["lon"],
                    self._map_pane.relayout_data["map.zoom"]
                    )
            self._map_pane.object = self.figure_data
        pn.bind(update_lead_time_scatter, self._lead_time_slider.param.value,
                watch=True)

        # Final layout
        return pn.Row(
            pn.Column(detail_card, site_card),
            map_card
        )
    
    def update_zoom(
            self,
            lat: float,
            lon: float,
            zoom: int = 7
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
    def selected_feature(self) -> Parameter:
        if self._left_feature_selector is None:
            raise RuntimeError("Must run generate before accessing parameter")
        return self._left_feature_selector.param.value
    
    @property
    def selected_metric(self) -> Parameter:
        if self._selected_metric is None:
            raise RuntimeError("Must run generate before accessing parameter")
        return self._selected_metric.param.value
    
    @property
    def selected_lead_time(self) -> Parameter:
        if self._lead_time_slider is None:
            raise RuntimeError("Must run generate before accessing parameter")
        return self._lead_time_slider.param.value

def get_site_selector() -> pn.Row:
    # ifile = "data/ABRFC.evaluation.csv.gz"
    ifile = "data/EANA/ABRFC.evaluation.csv.gz"
    return SiteSelector(
        model_name="NWM Medium Range Deterministic",
        evaluation_data=EvaluationCSVManager([ifile])
    ).generate()

# pn.serve(get_site_selector)

ifile = "data/EANA/ABRFC.evaluation.csv.gz"

df = pl.scan_csv(
    ifile,
    schema_overrides=DTYPE_MAPPING,
    null_values=[
        "-1000000000-01-01T00:00:00Z",
        "+1000000000-12-31T23:59:59.999999999Z",
        "PT-2562047788015215H-30M-8S",
        "PT2562047788015215H30M7.999999999S"
    ]
    ).filter(
    pl.col("METRIC NAME") == "BIAS FRACTION",
    pl.col("EVENT THRESHOLD NAME") == "RETRO_Q0",
    # pl.col("EVENT THRESHOLD NAME").is_null(),
    pl.col("SAMPLE QUANTILE").is_null(),
    pl.col("EARLIEST LEAD DURATION EXCLUSIVE").is_null(),
    pl.col("LEFT FEATURE NAME") == "07083710"
).head().collect().write_csv("test.csv")

import polars as pl
import polars.datatypes as pldt
import numpy as np

ifiles: list[str] = ["data/ABRFC.evaluation.csv.gz"]

dtype_mapping: dict[str, pl.DataType] = {
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

evaluation_period: int = 90
metric_name: str = "BIAS FRACTION"
sample_quantile: float = np.nan
earliest_lead_time: int = 0

data = pl.scan_csv(
    ifiles,
    schema_overrides=dtype_mapping
    ).with_columns(
        (pl.col("LATEST ISSUED TIME INCLUSIVE") -
         pl.col("EARLIEST ISSUED TIME EXCLUSIVE")
         ).alias("EVALUATION PERIOD")
    ).filter(
        pl.col("EVALUATION PERIOD") == pl.duration(days=evaluation_period)
    ).filter(
        pl.col("METRIC NAME") == metric_name
    ).filter(
        pl.col("SAMPLE QUANTILE").is_null()
    ).with_columns(
        pl.col("EARLIEST LEAD DURATION EXCLUSIVE"
               ).str.extract("(\\d+)").alias(
                   "EARLIEST LEAD TIME").cast(pldt.Int32),
        pl.col("LATEST LEAD DURATION INCLUSIVE"
               ).str.extract("(\\d+)").alias(
                   "LATEST LEAD TIME").cast(pldt.Int32)
    ).filter(
        pl.col("EARLIEST LEAD TIME") == earliest_lead_time
    )

import geopandas as gpd

custom_data = data.select(
    pl.col("LEFT FEATURE DESCRIPTION"),
    pl.col("LEFT FEATURE NAME"),
    pl.col("RIGHT FEATURE NAME"),
    pl.col("STATISTIC"),
    pl.col("LEFT FEATURE WKT")
).collect().to_pandas()
geometry = gpd.GeoSeries.from_wkt(
    custom_data["LEFT FEATURE WKT"]
)
custom_data["LATITUDE"] = geometry.y
custom_data["LONGITUDE"] = geometry.x
start_date = data.select(
    pl.col("EARLIEST ISSUED TIME EXCLUSIVE")
).min().collect().item(row=0, column=0)
end_date = data.select(
    pl.col("LATEST ISSUED TIME INCLUSIVE")
).min().collect().item(row=0, column=0)

import plotly.graph_objects as go
import colorcet as cc

# Build figure
selected_marker = go.Scattermap(
    showlegend=False,
    name="",
    lat=custom_data["LATITUDE"].iloc[:1],
    lon=custom_data["LONGITUDE"].iloc[:1],
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

# Add Map
scatter_map = go.Scattermap(
    showlegend=False,
    name="",
    lat=custom_data["LATITUDE"],
    lon=custom_data["LONGITUDE"],
    mode="markers",
    marker=dict(
        size=15,
        color=custom_data["STATISTIC"],
        colorscale=cc.gouldian,
        colorbar=dict(title=dict(text="Bias Fraction<br>(0 to 24 hours)")),
        cmin=-1.0,
        cmax=1.0
        ),
    customdata=custom_data,
    hovertemplate=
    "%{customdata[0]}<br>"
    "USGS Site Code: %{customdata[1]}<br>"
    "NWM Feature ID: %{customdata[2]}<br>"
    "Longitude: %{lon}<br>"
    "Latitude: %{lat}<br><br>"
    "Bias Fraction: %{marker.color:.2f}<br>"
)

# Layout configuration
layout = go.Layout(
    showlegend=False,
    height=720,
    width=1280,
    margin=dict(l=0, r=0, t=50, b=0),
    map=dict(
        style="satellite-streets",
        center={
            "lat": custom_data["LATITUDE"].mean(),
            "lon": custom_data["LONGITUDE"].mean()
            },
        zoom=3
    ),
    clickmode="event",
    modebar=dict(
        remove=["lasso", "select"]
    ),
    dragmode="zoom"
)

import panel as pn

patch = {
    "data": [selected_marker, scatter_map],
    "layout": layout
}

map_pane = pn.pane.Plotly(patch)
left_feature_selector = pn.widgets.AutocompleteInput(
    name="USGS Site Code",
    options=custom_data["LEFT FEATURE NAME"].to_list(),
    search_strategy="includes",
    placeholder="Enter USGS site code"
)
right_feature_selector = pn.widgets.AutocompleteInput(
    name="NWM Feature ID",
    options=custom_data["RIGHT FEATURE NAME"].to_list(),
    search_strategy="includes",
    placeholder="Enter NWM feature ID"
)

def update_zoom_selection(
        lat: float,
        lon: float,
        zoom: int = 5):
    layout["map"]["center"].update({
        "lat": lat,
        "lon": lon
    })
    layout["map"].update({
        "zoom": zoom
    })
    map_pane.relayout_data.update({"map.center": {"lat": lat, "lon": lon}})
    map_pane.relayout_data.update({"map.zoom": zoom})

map_clicked = False
left_trigger = False
right_trigger = False
def update_selection(event, source: str):
    global map_clicked
    global left_trigger
    global right_trigger
    if source == "click_data":
        point = event["points"][0]
        lon = point["lon"]
        lat = point["lat"]
        map_clicked = True
        left_feature_selector.value = point["customdata"][1]
        right_feature_selector.value = point["customdata"][2]
        map_clicked = False
        if "map.center" in map_pane.relayout_data:
            update_zoom_selection(
                map_pane.relayout_data["map.center"]["lat"],
                map_pane.relayout_data["map.center"]["lon"],
                map_pane.relayout_data["map.zoom"]
                )
    elif source == "left_value":
        if map_clicked or right_trigger:
            return
        site_info = custom_data[custom_data["LEFT FEATURE NAME"] == event]
        lon = site_info["LONGITUDE"].iloc[0]
        lat = site_info["LATITUDE"].iloc[0]
        left_trigger = True
        right_feature_selector.value = site_info["RIGHT FEATURE NAME"].iloc[0]
        left_trigger = False
        update_zoom_selection(lat, lon)
    elif source == "right_value":
        if map_clicked or left_trigger:
            return
        site_info = custom_data[custom_data["RIGHT FEATURE NAME"] == event]
        lon = site_info["LONGITUDE"].iloc[0]
        lat = site_info["LATITUDE"].iloc[0]
        right_trigger = True
        left_feature_selector.value = site_info["LEFT FEATURE NAME"].iloc[0]
        right_trigger = False
        update_zoom_selection(lat, lon)
    selected_marker.update({
        "lat": [lat], "lon": [lon]
    })
    if selected_marker["marker"]["size"] != 25:
        selected_marker["marker"].update({"size": 25})
    map_pane.object = patch
pn.bind(update_selection,
        map_pane.param.click_data, watch=True, source="click_data")
pn.bind(update_selection,
        left_feature_selector.param.value, watch=True, source="left_value")
pn.bind(update_selection,
        right_feature_selector.param.value, watch=True, source="right_value")

detail_card = pn.Card(
    pn.pane.Markdown(
        "**Configuration**: Medium Range<br>"
        f"**Start date**: {start_date}<br>"
        f"**End date**: {end_date}<br>"
    ),
    title="Evaluation Details",
    collapsible=False,
    margin=10,
    width=325
)
site_card = pn.Card(
    left_feature_selector,
    right_feature_selector,
    collapsible=False,
    title="Site Selection",
    margin=10,
    width=325
)
map_card = pn.Card(
    map_pane,
    collapsible=False,
    title="Site Map",
    margin=10
)

pn.serve(pn.Row(
    pn.Column(detail_card, site_card),
    map_card
))

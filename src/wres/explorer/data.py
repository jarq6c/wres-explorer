"""Methods to load and process WRES output."""
from typing import Type, Iterable
import pandas as pd
import geopandas as gpd

WRES_COLUMNS: dict[str, Type] = {
    "LEFT VARIABLE NAME": "category",
    "RIGHT VARIABLE NAME": "category",
    "BASELINE VARIABLE NAME": str,
    "COVARIATE FILTERS": str,
    "POOL NUMBER": int,
    "EVALUATION SUBJECT": "category",
    "FEATURE GROUP NAME": "category",
    "LEFT FEATURE NAME": "category",
    "LEFT FEATURE WKT": "category",
    "LEFT FEATURE SRID": "category",
    "LEFT FEATURE DESCRIPTION": "category",
    "RIGHT FEATURE NAME": "category",
    "RIGHT FEATURE WKT": "category",
    "RIGHT FEATURE SRID": "category",
    "RIGHT FEATURE DESCRIPTION": "category",
    "BASELINE FEATURE NAME": "category",
    "BASELINE FEATURE WKT": "category",
    "BASELINE FEATURE SRID": "category",
    "BASELINE FEATURE DESCRIPTION": "category",
    "EARLIEST ISSUED TIME EXCLUSIVE": "datetime",
    "LATEST ISSUED TIME INCLUSIVE": "datetime",
    "EARLIEST VALID TIME EXCLUSIVE": "datetime",
    "LATEST VALID TIME INCLUSIVE": "datetime",
    "EARLIEST LEAD DURATION EXCLUSIVE": "category",
    "LATEST LEAD DURATION INCLUSIVE": "category",
    "TIME SCALE DURATION": "category",
    "TIME SCALE FUNCTION": "category",
    "TIME SCALE START MONTH-DAY INCLUSIVE": str,
    "TIME SCALE END MONTH-DAY INCLUSIVE": str,
    "EVENT THRESHOLD NAME": str,
    "EVENT THRESHOLD LOWER VALUE": "numeric",
    "EVENT THRESHOLD UPPER VALUE": str,
    "EVENT THRESHOLD UNITS": str,
    "EVENT THRESHOLD LOWER PROBABILITY": str,
    "EVENT THRESHOLD UPPER PROBABILITY": str,
    "EVENT THRESHOLD SIDE": "category",
    "EVENT THRESHOLD OPERATOR": "category",
    "DECISION THRESHOLD NAME": str,
    "DECISION THRESHOLD LOWER VALUE": str,
    "DECISION THRESHOLD UPPER VALUE": str,
    "DECISION THRESHOLD UNITS": str,
    "DECISION THRESHOLD LOWER PROBABILITY": str,
    "DECISION THRESHOLD UPPER PROBABILITY": str,
    "DECISION THRESHOLD SIDE": str,
    "DECISION THRESHOLD OPERATOR": str,
    "METRIC NAME": "category",
    "METRIC COMPONENT NAME": "category",
    "METRIC COMPONENT QUALIFIER": str,
    "METRIC COMPONENT UNITS": "category",
    "METRIC COMPONENT MINIMUM": "numeric",
    "METRIC COMPONENT MAXIMUM": "numeric",
    "METRIC COMPONENT OPTIMUM": "numeric",
    "STATISTIC GROUP NUMBER": int,
    "SUMMARY STATISTIC NAME": "category",
    "SUMMARY STATISTIC COMPONENT NAME": "category",
    "SUMMARY STATISTIC UNITS": "category",
    "SUMMARY STATISTIC DIMENSION": "category",
    "SUMMARY STATISTIC QUANTILE": str,
    "SAMPLE QUANTILE": "numeric",
    "STATISTIC": "numeric",
    "EVALUATION PERIOD": "category",
    "LEAD TIME": "category"
}
"""WRES columns and data types."""

def load_dataframes(
        filepaths: Iterable[str],
        type_mapping: dict[str, Type] = WRES_COLUMNS
        ) -> pd.DataFrame:
    """
    Load CSV output and return optimized dataframe.
    
    Parameters
    ----------
    filepaths: Iterable[str], required
        Paths to files.
    type_mapping: dict[str, Type], optional
        Mapping from column label to data type.
    
    Returns
    -------
    pandas.DataFrame
    """
    data = pd.concat(
        [pd.read_csv(fp, dtype=str) for fp in filepaths],
        ignore_index=True
        )

    drop = []
    for c in data:
        if data[c].isna().all():
            drop.append(c)
            continue

        if type_mapping[c] == "datetime":
            data[c] = pd.to_datetime(data[c])
            continue

        if type_mapping[c] == "numeric":
            data[c] = pd.to_numeric(data[c], errors="coerce")
            continue

        if type_mapping[c] == "geometry":
            data[c] = gpd.GeoSeries.from_wkt(data[c])
            continue

        data[c] = data[c].astype(type_mapping[c])

    data["EVALUATION PERIOD"] = (
        data["LATEST ISSUED TIME INCLUSIVE"] -
        data["EARLIEST ISSUED TIME EXCLUSIVE"]
    ).astype(str).astype("category")
    earliest = data["EARLIEST LEAD DURATION EXCLUSIVE"].str.extract("(\\d+)")
    latest = data["LATEST LEAD DURATION INCLUSIVE"].str.extract("(\\d+)")
    data["LEAD HOURS MIN"] = earliest.astype(int)
    data["LEAD HOURS MAX"] = latest.astype(int)

    return data.drop(drop, axis=1)

class DataManager:
    """
    Handle the data loading and processing.

    Attributes
    ----------
    data: pd.DataFrame
        Data loaded from the CSV files.
    feature_mapping: pd.DataFrame
        Mapping of features to their descriptions and geometries.
    """
    def __init__(self):
        self.data: pd.DataFrame = None
        self.feature_mapping: pd.DataFrame = None
    
    def load_data(self, filepaths: list[str]):
        if len(filepaths) == 0:
            self.data = pd.DataFrame({"message": ["no data loaded"]})
            self.feature_mapping = pd.DataFrame(
                {"message": ["no data loaded"]})
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

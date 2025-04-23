import panel as pn
import pandas as pd
from src.wres.explorer.data import load_dataframes

pn.extension("tabulator")

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

    # Data table tab
    data: pd.DataFrame = None
    feature_map: pd.DataFrame = None
    def update_data_table(event):
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
                    "RIGHT FEATURE NAME",
                    "LEFT FEATURE WKT"
                    ]].drop_duplicates().astype(str)
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
    tabs.append(("Data Table", pn.bind(update_data_table, load_data)))

    # Site selector tab
    left_feature_name: str = None
    right_feature_name: str = None
    def update_map(event):
        nonlocal feature_map
        nonlocal left_feature_name
        nonlocal right_feature_name
        if not event:
            return update_data_table(event)
        if len(files.value) == 0:
            return update_data_table(event)
        
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
        pn.bind(update_left_feature, right=right_feature, watch=True)
        
        # Layout
        return pn.Column(
            left_feature,
            right_feature
        )
    tabs.append(("Site Selector", pn.bind(update_map, load_data)))

    # Build and serve the dashboard
    dashboard = pn.template.BootstrapTemplate(title="WRES Explorer")
    dashboard.main.append(tabs)
    pn.serve(dashboard.servable())

if __name__ == "__main__":
    run()

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
    load_data = pn.widgets.Button(name="Load data", button_type="primary")
    tabs.append(("Files", pn.Column(files, load_data)))

    # Data tab
    data = pd.DataFrame({"message": ["no data loaded"]})
    def update_data_table(event):
        nonlocal data
        if not event:
            data = pd.DataFrame({"message": ["no data loaded"]})
        if len(files.value) == 0:
            data = pd.DataFrame({"message": ["no data loaded"]})
        else:
            try:
                data = load_dataframes(files.value)
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
    tabs.append(("Data", pn.bind(update_data_table, load_data)))

    # Map tab
    def update_map(event):
        nonlocal data
        if not event:
            return "No data selected"
        
        return f"{len(data.index)}"
    tabs.append(("Map", pn.bind(update_map, load_data)))

    dashboard = pn.template.BootstrapTemplate(title="WRES Explorer")
    dashboard.main.append(tabs)
    pn.serve(dashboard.servable())

if __name__ == "__main__":
    run()

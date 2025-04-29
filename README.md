# WRES Explorer
Utilities to visualize and explore output from the [NOAA Office of Water Prediction](https://github.com/NOAA-OWP)'s (OWP) [Water Resources Evaluation Service](https://github.com/NOAA-OWP/wres) (WRES).

## Installation
In accordance with the python community, we support and advise the usage of virtual
environments in any workflow using python. In the following installation guide, we
use python's built-in `venv` module to create a virtual environment in which the
tool will be installed. Note this is just personal preference, any python virtual
environment manager should work just fine (`conda`, `pipenv`, etc. ).

```bash
# Create and activate python environment, requires python >= 3.10
$ python3 -m venv venv
$ source venv/bin/activate
$ python3 -m pip install --upgrade pip wheel

# Install nwis_client
$ python3 -m pip install wres.explorer
```

## Usage
```console
Usage: wres-explorer [OPTIONS]

  Visualize and explore metrics output from WRES CSV2 formatted output.

  Run "wres-explorer" from the command-line, ctrl+c to stop the server.:

Options:
  --help  Show this message and exit.
```

## Application Interface
The application features a tabbing interface. The "File Selector" tab is active by default. 

### File Selector
The file browser starts in the directory where the application was launched. Use the arrows (`>>` or `<<`) to move the files you want to visualize from the "File Browser" to the "Selected files".
![File Selector](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/file_selector.JPG)

The example below has selected the files `ABRFC.evaluation.csv.gz` and `ABRFC.pairs.csv.gz`. After selecting one or more files, click the "Load/Reload Data" button to read the files.
![File Selected](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/file_selection.JPG)

### Feature Selector
To inspect the metrics at a specific feature (site), you need to select a feature from the selection boxes or by clicking on the map. The available options are determined by the features found in the files you selected earlier. Note the selected site in magenta.
![Map Selector](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/map_selector.JPG)

### Metrics Plots
After a site is selected, the "Metrics Plots" tab will be populated with plots showing the metrics found at this feature. Use the dropdown menu ("Select Metric") to view different metrics. Selecting a site will filter this table to the selected feature.
![Metrics Plot](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/metric_selector.JPG)

### Pairs Plots
After a site is selected, the "Pairs Plots" tab will be populated with plots showing the pairs (time series).
![Pairs Plots](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/pairs_plot.JPG)

### Metrics Table
Once data are loaded, you will be able to explore the metrics file(s) contents through a paging tabular interface shown below. Selecting a site will filter this table to the selected feature.
![Metrics Table](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/data_table.JPG)

### Pairs Table
Once data are loaded, you will be able to explore the pairs file(s) contents through a paging tabular interface shown below. Selecting a site will filter this table to the selected feature.
![Pairs Table](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/pairs_table.JPG)

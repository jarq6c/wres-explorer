# WRES Explorer
Utilities to visualize and explore output from the [NOAA Office of Water Prediction's](https://github.com/NOAA-OWP) (OWP) [Water Resources Evaluation Service](https://github.com/NOAA-OWP/wres) (WRES). The primary use-case for these tools is to support the routine evaluation of the [National Water Model](https://water.noaa.gov/about/nwm).

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

# Install wres.explorer
$ python3 -m pip install wres.explorer
```

## Usage
```console
Usage: wres-explorer [OPTIONS]

  Visualize and explore output from WRES CSV2 formatted files.

  Run "wres-explorer" from the command-line, ctrl+c to stop the server.:

Options:
  --help  Show this message and exit.
```

## Application Interface
The application features a tabbing interface. The "CSV Selector" tab is active by default. 

### CSV Selector
The file browser starts in the directory where the application was launched. Use the arrows (`>>` or `<<`) to move the files you want to visualize from the "File Browser" to the "Selected files".
![CSV Selector](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/file_selector.JPG)

The example below has selected the files `ABRFC.evaluation.csv.gz` and `ABRFC.pairs.csv.gz`. After selecting one or more files, click the "Load/Reload Data" button to read the files.
![File Selected](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/file_selection.JPG)

### Feature Selector
To inspect the metrics at a specific feature (site), you need to select a feature from the selection boxes or by clicking on the map. The available options are determined by the features found in the files you selected earlier. Note the selected site in magenta.
![Map Selector](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/map_selector.JPG)

### Metrics Plots
After a site is selected, the "Metrics Plots" tab will be populated with plots showing the metrics found at this feature. Use the dropdown menu ("Select Metric") to view different metrics.
![Metrics Plot](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/metric_selector.JPG)

### Pairs Plots
After a site is selected, the "Pairs Plots" tab will be populated with plots showing the pairs (time series) for the selected feature.
![Pairs Plots](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/pairs_plot.JPG)

### Metrics Table
Once data are loaded, you will be able to explore the metrics file(s) contents through a paging tabular interface shown below.
![Metrics Table](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/data_table.JPG)

### Pairs Table
You can also explore the pairs file(s) contents through a paging tabular interface.
![Pairs Table](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/pairs_table.JPG)

### Image Selector
You can use the image selector tab to select and load WRES `.png` files for display and exploration. Selecting one or more image files and clicking "Load/Reload Images" will populate the "Image Viewer."
![Image Selector](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/image_selection.JPG)

### Image Viewer
The "Image Viewer" includes a carousel style image browser for exploring WRES plots.
![Image Viewer](https://raw.githubusercontent.com/jarq6c/wres-explorer/main/images/image_viewer.JPG)

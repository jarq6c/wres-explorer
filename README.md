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
$ python3 -m pip install --upgrade pip

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

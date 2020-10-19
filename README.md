# jupyterlab server

[![Tests](https://github.com/jupyterlab/jupyterlab_server/workflows/Tests/badge.svg)](https://github.com/jupyterlab/jupyterlab_server/actions?query=workflow%3ATests)
[![Coverage](https://codecov.io/gh/jupyterlab/jupyterlab_server/branch/master/graph/badge.svg)](https://codecov.io/gh/jupyterlab/jupyterlab_server)

https://github.com/jupyterlab/jupyterlab_server

## Install

`pip install jupyterlab_server`

## Usage
The application author creates a JupyterLab build on their machine
using the core JupyterLab application.  They can then serve their
files by subclassing the `LabServerApp` with the appropriate
configuration and creating a Python entry point that launches the app.


## Development Install

``` shell
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
pip install -e .
```

## Testing

To create a local test setup run the following commands:

``` shell
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
python3 -m venv venv
source venv/bin/activate
pip install -e .[test]
pytest
```

If you do not wish to create a virtual environment, you can run the following commands instead:

``` shell
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
pip install -e .[test]
pytest
```

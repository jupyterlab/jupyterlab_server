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

```
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
pip install -e .
```

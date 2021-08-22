# Development Install

``` shell
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
pip install -e .
```

# Testing

It is probably best to create a virtual environment to create a local test setup. There are multiple tools for creating a Python virtual environment out there from which you can choose the one you like best.

To create a local test setup run the following commands (inside your virtual environment, if you chose to create one):

``` shell
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
pip install -e .[test]  # install test dependencies
pytest --pyargs jupyterlab_server
```

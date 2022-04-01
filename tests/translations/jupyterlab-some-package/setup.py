from setuptools import setup

setup(
    name="jupyterlab-some-package",
    version="0.1.0",
    packages=["jupyterlab_some_package"],
    include_package_data=True,
    entry_points={"jupyterlab.locale": ["jupyterlab_some_package = jupyterlab_some_package"]},
)

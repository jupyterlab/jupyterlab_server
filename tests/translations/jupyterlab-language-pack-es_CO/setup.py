from setuptools import setup

setup(
    name="jupyterlab_language_pack_es_CO",
    version="0.1.0",
    packages=["jupyterlab_language_pack_es_CO"],
    include_package_data=True,
    entry_points={
        "jupyterlab.languagepack": [
            "es_CO = jupyterlab_language_pack_es_CO",
        ]
    },
)

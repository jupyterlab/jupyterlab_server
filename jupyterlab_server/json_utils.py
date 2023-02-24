# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import pathlib
from typing import Any, Dict, Union

import json5


def load_json(path: Union[pathlib.Path, str]) -> Dict[Any, Any]:
    """Load a json(5) file and return its contents.

    Assumes the file is UTF-8 encoded.

    Parameters
    ----------
    path : Path | str
        Path of the json or json5 file to load.

    Returns
    -------
    Dict[Any, Any]
        JSON content of the file, deserialized to a dictionary
    """
    with open(path, encoding="utf-8") as f:
        return json5.load(f)

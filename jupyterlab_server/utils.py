# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# created new file called utils.py to keep utility functions like _camelcase organized
def _camelCase(snake_str: str) -> str:
    """Convert snake_case string to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])

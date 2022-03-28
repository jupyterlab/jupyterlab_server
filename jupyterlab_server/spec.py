import os
from pathlib import Path

from ruamel.yaml import YAML
from openapi_core import create_spec

HERE = Path(os.path.dirname(__file__)).resolve()
path = HERE / 'rest-api.yml'
yaml = YAML(typ='safe')
openapi_spec_dict = yaml.load(path.read_text(encoding='utf-8'))
openapi_spec = create_spec(openapi_spec_dict)

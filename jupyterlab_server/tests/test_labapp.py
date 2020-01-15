"""Basic tests for the lab handlers.
"""

import pytest


@pytest.fixture
def notebooks(create_notebook):
    nbpaths = (
        'notebook1.ipynb',
        'jlab_test_notebooks/notebook2.ipynb',
        'jlab_test_notebooks/level2/notebook3.ipynb'
    )
    for nb in nbpaths:
        create_notebook(nb)
    return nbpaths


async def test_lab_handler(notebooks, fetch, labserverapp):
    r = await fetch('lab', 'jlab_test_notebooks')
    assert r.code == 200

    # Check that the lab template is loaded
    html = r.body.decode()
    assert "Files" in html
    assert "Running" in html
    assert "Clusters" in html


async def test_notebook_handler(notebooks, fetch, notebookapp):
    for nbpath in notebooks:
        r = await fetch('notebooks', nbpath)
        assert r.code == 200
        # Check that the notebook template is loaded
        html = r.body.decode()
        assert "Menu" in html
        assert "Kernel" in html
        assert nbpath in html


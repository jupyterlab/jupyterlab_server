# Making a JupyterLab Server Release

## Using `jupyter_releaser`

The recommended way to make a release is to use [`jupyter_releaser`](https://github.com/jupyter-server/jupyter_releaser#checklist-for-adoption).

## Manual Release

### Set up
```
pip install tbump twine build
git pull origin $(git branch --show-current)
git clean -dffx
```

### Update the version and apply the tag
```
echo "Enter new version"
read script_version
tbump ${script_version}
```

### Build the artifacts
```
rm -rf dist
python -m build .
```

### Publish the artifacts to pypi
```
twine check dist/*
twine upload dist/*
```

# Making a JupyterLab Server Release

## Using `jupyter_releaser`

The recommended way to make a release is to use [`jupyter_releaser`](https://jupyter-releaser.readthedocs.io/en/latest/get_started/making_release_from_repo.html)

## Manual Release

### Set up

```
pip install pipx
git pull origin $(git branch --show-current)
git clean -dffx
```

### Update the version and apply the tag

```
echo "Enter new version"
read script_version
pipx run hatch version ${script_version}
git tag -a ${script_version} -m ${script_version}
```

### Build the artifacts

```
rm -rf dist
pipx run build .
```

### Publish the artifacts to pypi

```
pipx run twine check dist/*
pipx run twine upload dist/*
```

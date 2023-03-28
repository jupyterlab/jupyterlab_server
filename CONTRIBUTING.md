# Contributing

If you're reading this section, you're probably interested in contributing to
Jupyter. Welcome and thanks for your interest in contributing!

Please take a look at the Contributor documentation, familiarize yourself with
using the Jupyter Server, and introduce yourself on the mailing list and
share what area of the project you are interested in working on.

For general documentation about contributing to Jupyter projects, see the
[Project Jupyter Contributor Documentation](https://jupyter.readthedocs.io/en/latest/contributing/content-contributor.html).

## Development Install

```shell
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
pip install -e .
```

## Testing

It is probably best to create a virtual environment to create a local test setup. There are multiple tools for creating a Python virtual environment out there from which you can choose the one you like best.

To create a local test setup run the following commands (inside your virtual environment, if you chose to create one):

```shell
git clone https://github.com/jupyterlab/jupyterlab_server.git
cd jupyterlab_server
pip install -e .[test]  # install test dependencies
hatch run cov:test # optionally, arguments of the pytest CLI can be added
```

## Code Styling

`jupyterlab_server` has adopted automatic code formatting so you shouldn't
need to worry too much about your code style.
As long as your code is valid,
the pre-commit hook should take care of how it should look.
`pre-commit` and its associated hooks will automatically be installed when
you run `pip install -e ".[test]"`

To install `pre-commit` manually, run the following::

```shell
pip install pre-commit
pre-commit install
```

You can invoke the pre-commit hook by hand at any time with:

```shell
pre-commit run
```

which should run any autoformatting on your code
and tell you about any errors it couldn't fix automatically.
You may also install [black integration](https://github.com/psf/black#editor-integration)
into your text editor to format code automatically.

If you have already committed files before setting up the pre-commit
hook with `pre-commit install`, you can fix everything up using
`pre-commit run --all-files`. You need to make the fixing commit
yourself after that.

Some of the hooks only run on CI by default, but you can invoke them by
running with the `--hook-stage manual` argument.

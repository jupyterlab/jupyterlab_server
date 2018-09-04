#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import io
import os
from os.path import join as pjoin
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from setuptools.command.develop import develop
from setuptools.command.bdist_egg import bdist_egg
import sys

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None


# ---------------------------------------------------------------------------
# Top Level Variables
# ---------------------------------------------------------------------------

here = os.path.abspath(os.path.dirname(__file__))
is_repo = os.path.exists(pjoin(here, '.git'))
name = 'jupyterlab_server'

version_ns = {}
with io.open(pjoin(here, name, '_version.py'), encoding='utf8') as f:
    exec(f.read(), {}, version_ns)
__version__ = version_ns['__version__']


# ---------------------------------------------------------------------------
# Public Functions
# ---------------------------------------------------------------------------

def create_cmdclass(data_dirs=None):
    """Create a command class with the given optional wrappers.

    Parameters
    ----------
    wrappers: list(str), optional
        The cmdclass names to run before running other commands
    data_dirs: list(str), optional.
        The directories containing static data.
    """
    egg = bdist_egg if 'bdist_egg' in sys.argv else bdist_egg_disabled
    cmdclass = dict(
        build_py=build_py,
        sdist=sdist,
        bdist_egg=egg,
        develop=develop
    )
    if bdist_wheel:
        cmdclass['bdist_wheel'] = bdist_wheel
    return cmdclass


class bdist_egg_disabled(bdist_egg):
    """Disabled version of bdist_egg
    Prevents setup.py install performing setuptools' default easy_install,
    which it should never ever do.
    """

    def run(self):
        sys.exit('Aborting implicit building of eggs. Use `pip install .` ' +
                 ' to install from source.')

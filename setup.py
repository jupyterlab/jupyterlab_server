#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from setuptools import setup, find_packages
import sys
from setupbase import create_cmdclass, __version__

setup_args = dict(
    name='jupyterlab_server',
    version=__version__,
    packages=find_packages('.'),
    description='Jupyter Server',
    long_description="""
    This package is used to launch an application built using JupyterLab
    """,
    author='Jupyter Development Team',
    author_email='jupyter@googlegroups.com',
    url='http://jupyter.org',
    license='BSD',
    platforms='Linux, Mac OS X, Windows',
    keywords=['Jupyter', 'JupyterLab'],
    cmdclass=create_cmdclass(),
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    include_package_data=True
)

if 'setuptools' in sys.modules:
    setup_args['python_requires'] = '>=3.5'
    setup_args['extras_require'] = {'test': ['pytest', 'requests']}
    setup_args['install_requires'] = ['jsonschema>=2.6.0', 'notebook>=4.2.0']

if __name__ == '__main__':
    setup(**setup_args)

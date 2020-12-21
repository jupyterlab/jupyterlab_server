#!/usr/bin/env python
# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from setupbase import create_cmdclass, __version__
from setuptools import find_packages, setup
import sys


setup_args = dict(
    name='jupyterlab_server',
    version=__version__,
    packages=find_packages('.'),
    description='JupyterLab Server',
    long_description=open('./README.md').read(),
    long_description_content_type='text/markdown',
    author='Jupyter Development Team',
    author_email='jupyter@googlegroups.com',
    url='https://jupyter.org',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    include_package_data=True
)

if 'setuptools' in sys.modules:
    setup_args['python_requires'] = '>=3.6'
    setup_args['extras_require'] = {
        'test': [
            'codecov',
            'ipykernel',
            'pytest>=5.3.2',
            'pytest-cov',
            'jupyter_server[test]',
            'pytest-console-scripts',
            'strict-rfc3339',
            'wheel',
        ],
    }
    setup_args['install_requires'] = [
        'babel',
        'jinja2>=2.10',
        'json5',
        'jsonschema>=3.0.1',
        'packaging',
        'requests',
        'jupyter_server~=1.1',
    ]

if __name__ == '__main__':
    setup(**setup_args)

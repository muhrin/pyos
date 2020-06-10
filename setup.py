# -*- coding: utf-8 -*-
from setuptools import setup

__author__ = "Martin Uhrin"
__license__ = "GPLv3"
__contributors__ = "Sonia Collaud"

about = {}
with open('pyos/version.py') as f:
    exec(f.read(), about)

setup(
    name='pyos',
    version=about['__version__'],
    description="Browse python objects as if they were files on disk",
    long_description=open('README.rst').read(),
    url='https://github.com/muhrin/pyos.git',
    author='Martin Uhrin',
    author_email='martin.uhrin.10@ucl.ac.uk',
    license=__license__,
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='database schemaless nosql object-store',
    install_requires=[
        'anytree',
        'columnize',
        'mincepy>=0.13.0, <0.15.0',
        'click',
        'tabulate',
        'ipython',
        'pyprnt',
        'tqdm',
    ],
    extras_require={
        'gui': ['mincepy[gui]'],
        'dev': [
            'ipython',
            'jupyter-sphinx',
            'nbsphinx',
            'pip',
            'pytest>4',
            'pytest-cov',
            'pre-commit',
            'sphinx',
            'sphinx-autobuild',
            'yapf',
            'prospector',
            'pylint',
            'twine',
        ],
    },
    packages=['pyos', 'pyos.db', 'pyos.fs', 'pyos.os', 'pyos.psh', 'pyos.psh.cmds', 'pyos.psh_lib'],
    project_urls={
        'Documentation': 'https://pyos.readthedocs.org/',
        'Source': 'https://github.com/muhrin/pyos/',
    },
    include_package_data=True,
    test_suite='test',
    entry_points={'mincepy.plugins.types': ['pyos_types = pyos.provides:get_types',]})

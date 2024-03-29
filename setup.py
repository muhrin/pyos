# -*- coding: utf-8 -*-
from setuptools import setup

__author__ = 'Martin Uhrin'
__license__ = 'GPLv3'
__contributors__ = 'Sonia Collaud'

about = {}
with open('pyos/version.py') as f:
    exec(f.read(), about)

setup(
    name='pyos',
    version=about['__version__'],
    description='Browse python objects as if they were files on disk',
    long_description=open('README.rst').read(),
    url='https://github.com/muhrin/pyos.git',
    author='Martin Uhrin',
    author_email='martin.uhrin.10@ucl.ac.uk',
    license=__license__,
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='database schemaless nosql object-store',
    python_requires='>=3.7',
    install_requires=[
        'anytree',
        'cmd2 ~= 1.3.2',
        'columnize',
        'mincepy>=0.16.1, <0.17',
        'click',
        'ipython',
        'pandas',
        'pymongo',
        'pyprnt',
        'pytray >= 0.3.0',
        'stevedore',
        'tqdm',
        'yarl',
    ],
    extras_require={
        'gui': ['mincepy[gui]'],
        'dev': [
            'cmd2-ext-test',
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
    entry_points={
        'console_scripts': ['pyos = pyos.cli:pyos', 'psh = pyos.cli:psh_'],
        'mincepy.plugins.types': ['pyos_types = pyos.provides:get_types',]
    })

# -*- coding: utf-8 -*-
from setuptools import setup

__author__ = "Martin Uhrin"
__license__ = "GPLv3 and MIT, see LICENSE file"

about = {}
with open('pyos/version.py') as f:
    exec(f.read(), about)

setup(name='pyos',
      version=about['__version__'],
      description="Browse python objects as if they were files on disk",
      long_description=open('README.rst').read(),
      url='https://github.com/muhrin/pyos.git',
      author='Martin Uhrin',
      author_email='martin.uhrin.10@ucl.ac.uk',
      license=__license__,
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      keywords='database schemaless nosql object-store',
      install_requires=[
          'anytree',
          'columnize',
          'mincepy>=0.10.4',
          'click',
          'tabulate',
          'ipython',
      ],
      extras_require={
          'gui': ['mincepy[gui]'],
          'dev': [
              'ipython',
              'pip',
              'pytest>4',
              'pytest-cov',
              'pre-commit',
              'yapf',
              'prospector',
              'pylint',
              'twine',
          ],
      },
      packages=[
          'pyos',
      ],
      include_package_data=True,
      test_suite='test',
      entry_points={'mincepy.plugins.types': ['pyos_types = pyos.provides:get_types',]})

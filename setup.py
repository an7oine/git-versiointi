# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

from versiointi import _versionumero

with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
  long_description = f.read()

setup(
  name='git-versiointi',
  version=_versionumero(os.path.dirname(__file__)),
  description='Asennettavan pakettiversion haku git-leimojen mukaan',
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/an7oine/git-versiointi.git',
  author='Antti Hautaniemi',
  author_email='antti.hautaniemi@pispalanit.fi',
  licence='MIT',
  packages=find_packages(),
  py_modules=['_versiointi_setuptools_build_meta'],
  entry_points={
    'distutils.setup_keywords': [
      'git_versiointi = versiointi:tarkista_git_versiointi',
    ],
    'egg_info.writers': [
      'historia.json = versiointi.egg_info:kirjoita_json',
    ],
    'setuptools.finalize_distribution_options': [
      'versiointi = versiointi:finalize_distribution_options',
    ]
  },
  classifiers=[
    'Programming Language :: Python :: 3',
  ],
  install_requires=['GitPython', 'setuptools>=42'],
)

# -*- coding: utf-8 -*-

import os
import setuptools

setuptools._install_setup_requires({'setup_requires': ['GitPython']})
from versiointi import asennustiedot

with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
  long_description = f.read()

setuptools.setup(
  name='git-versiointi',
  description='Asennettavan pakettiversion haku git-leimojen mukaan',
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/an7oine/git-versiointi.git',
  author='Antti Hautaniemi',
  author_email='antti.hautaniemi@pispalanit.fi',
  packages=setuptools.find_packages(),
  entry_points={
    'distutils.setup_keywords': [
      'historia = versiointi.egg_info:varmista_json',
    ],
    'egg_info.writers': [
      'historia.json = versiointi.egg_info:kirjoita_json',
    ],
  },
  classifiers=[
    'Programming Language :: Python :: 3',
  ],
  **asennustiedot(__file__)
)

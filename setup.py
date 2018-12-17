# -*- coding: utf-8 -*-

import setuptools

setuptools._install_setup_requires({'setup_requires': ['GitPython']})
from versiointi import asennustiedot

setuptools.setup(
  name='git-versiointi',
  description='Asennettavan pakettiversion haku git-leimojen mukaan',
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

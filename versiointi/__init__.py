# -*- coding: utf-8 -*-

import configparser
from datetime import datetime
import os
import re
import sys
import warnings

from .repo import git_versio, git_historia


def vaatimukset(setup_py):
  '''
  Palauta `requirements.txt`-tiedostossa määritellyt asennusvaatimukset.
  '''
  requirements_txt = os.path.join(
    os.path.dirname(setup_py), 'requirements.txt'
  )
  return [
    # Poimi muut kuin tyhjät ja kommenttirivit.
    rivi
    for rivi in map(str.strip, open(requirements_txt))
    if rivi and not rivi.startswith('#')
  ] if os.path.isfile(requirements_txt) else []
  # def vaatimukset


def asennustiedot(setup_py, **kwargs):
  '''
  Palauta `setup()`-kutsulle annettavat lisäparametrit.
  '''
  # Muodosta setup()-parametrit.
  param = {}

  # Lisää asennusvaatimukset, jos on.
  requirements = vaatimukset(setup_py)
  if requirements:
    param['install_requires'] = [
      # Lisää paketin nimi kunkin `git+`-alkuisen rivin alkuun.
      re.sub(
        r'^(git\+(ssh|https).*/([^/.@]+)(\.git).*)$',
        r'\3 @ \1',
        rivi
      )
      for rivi in requirements
    ]
    # if requirements

  # Ota hakemiston nimi.
  polku = os.path.dirname(setup_py)

  # Lataa oletusparametrit `setup.cfg`-tiedostosta, jos on.
  c = configparser.ConfigParser()
  c.read(os.path.join(polku, 'setup.cfg'))
  if c.has_section('versiointi'):
    kwargs = {
      **kwargs,
      **dict(c['versiointi']),
    }

  try:
    ref_i = sys.argv.index('--ref', 0, -1)
  except ValueError:
    pass
  else:
    kwargs['ref'] = sys.argv[ref_i + 1]
    sys.argv[ref_i:ref_i+2] = []

  # Muodosta versionumero ja git-historia.
  try:
    param.update(dict(
      version=git_versio(polku, **kwargs),
      historia=git_historia(polku, **kwargs),
    ))
  except ValueError:
    warnings.warn('git-tietovarastoa ei löytynyt', RuntimeWarning)
    param['version'] = datetime.now().strftime('%Y%m%d.%H%M%s')
  return param
  # def asennustiedot

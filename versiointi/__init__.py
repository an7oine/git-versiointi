# -*- coding: utf-8 -*-

from datetime import datetime
import os
import re
import warnings


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

  try:
    from .repo import git_versio, git_historia
    # Ota hakemiston nimi.
    polku = os.path.dirname(setup_py)
    param.update(dict(
      version=git_versio(polku, **kwargs),
      historia=list(git_historia(polku, **kwargs)),
    ))
  except ValueError:
    warnings.warn('git-tietovarastoa ei löytynyt', RuntimeWarning)
    param['version'] = datetime.now().strftime('%Y%m%d.%H%M%s')
  return param
  # def asennustiedot

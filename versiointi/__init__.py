# -*- coding: utf-8 -*-

import configparser
from datetime import datetime
import os
import re
import warnings

from setuptools.command.build_py import build_py

from .parametrit import kasittele_parametrit
from .tiedostot import tiedostokohtainen_versiointi
from .versiointi import Versiointi


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

  Args:
    setup_py: setup.py-tiedoston nimi polkuineen (__file__)
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
  parametrit = configparser.ConfigParser()
  parametrit.read(os.path.join(polku, 'setup.cfg'))
  if parametrit.has_section('versiointi'):
    kwargs.update(dict(parametrit['versiointi']))
  if parametrit.has_section('versiointi.kaytanto'):
    kwargs['kaytanto'] = parametrit['versiointi.kaytanto']

  # Alusta versiointiolio.
  try:
    versiointi = Versiointi(polku, **kwargs)
  except ValueError:
    warnings.warn('git-tietovarastoa ei löytynyt', RuntimeWarning)
    return {'version': datetime.now().strftime('%Y%m%d.%H%M%s')}

  # Näytä pyydettäessä tulosteena paketin versiotiedot.
  # Paluuarvona saadaan komentoriviltä määritetty revisio.
  pyydetty_ref = kasittele_parametrit(versiointi)

  # Puukota `build_py`-komento huomioimaan tiedostokohtaiset
  # versiointimääritykset.
  tiedostokohtainen_versiointi(build_py, versiointi)

  # Muodosta versionumero ja git-historia.
  return {
    **param,
    'version': versiointi.versionumero(ref=pyydetty_ref),
    'historia': versiointi.historia(ref=pyydetty_ref),
  }
  # def asennustiedot

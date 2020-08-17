# -*- coding: utf-8 -*-

import configparser
from datetime import datetime
import os
import warnings

from setuptools.command.build_py import build_py

from .parametrit import kasittele_parametrit
from .tiedostot import tiedostokohtainen_versiointi
from .vaatimukset import asennusvaatimukset
from .versiointi import Versiointi


def asennustiedot(setup_py, **kwargs):
  '''
  Palauta `setup()`-kutsulle annettavat lisäparametrit.

  Args:
    setup_py: setup.py-tiedoston nimi polkuineen (__file__)
  '''
  # Muodosta setup()-parametrit.
  param = {}

  # Lisää asennusvaatimukset, jos on.
  requirements = asennusvaatimukset(setup_py)
  if requirements:
    param['install_requires'] = requirements
    # if requirements

  # Ota hakemiston nimi.
  polku = os.path.dirname(setup_py)

  # Lataa oletusparametrit `setup.cfg`-tiedostosta, jos on.
  parametrit = configparser.ConfigParser()
  parametrit.read(os.path.join(polku, 'setup.cfg'))
  if parametrit.has_section('versiointi'):
    kwargs = dict(**kwargs, **dict(parametrit['versiointi']))

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

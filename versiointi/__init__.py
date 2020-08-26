# -*- coding: utf-8 -*-

import configparser
from datetime import datetime
import functools
import os
import warnings

from setuptools.command import build_py as _build_py

from .parametrit import kasittele_parametrit
from .tiedostot import build_py
from .vaatimukset import asennusvaatimukset
from .versiointi import Versiointi


# Puukota `build_py`-komento huomioimaan tiedostokohtaiset
# versiointimääritykset.
_build_py.build_py = functools.wraps(_build_py.build_py, updated=())(
  type(_build_py.build_py)('build_py', (build_py, _build_py.build_py), {})
)

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

  # Aseta versiointi tiedostokohtaisen versioinnin määreeksi.
  _build_py.build_py.git_versiointi = versiointi

  # Muodosta versionumero ja git-historia.
  return {
    **param,
    'version': versiointi.versionumero(ref=pyydetty_ref),
    'historia': versiointi.historia(ref=pyydetty_ref),
  }
  # def asennustiedot

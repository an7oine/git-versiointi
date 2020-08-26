# -*- coding: utf-8 -*-

import configparser
import functools
import os
import sys

from distutils.errors import DistutilsSetupError
from setuptools.command import build_py as _build_py

from .parametrit import kasittele_parametrit
from .tiedostot import build_py
from .vaatimukset import asennusvaatimukset


# Puukota `build_py`-komento huomioimaan tiedostokohtaiset
# versiointimääritykset.
_build_py.build_py = functools.wraps(_build_py.build_py, updated=())(
  type(_build_py.build_py)('build_py', (build_py, _build_py.build_py), {})
)


def asennustiedot(setup_py):
  ''' Vanha käyttötapa.  '''
  requirements = asennusvaatimukset(setup_py)
  return {
    'git_versiointi': setup_py,
    **({'install_requires': requirements} if requirements else {})
  }
  # def asennustiedot


def tarkista_git_versiointi(dist, attr, value):
  ''' Hae Git-tietovarasto määritetyn setup.py-tiedoston polusta. '''
  # pylint: disable=unused-argument, protected-access
  from .versiointi import Versiointi

  if isinstance(value, Versiointi):
    # Hyväksytään aiemmin asetettu versiointiolio (tupla-ajo).
    return
  elif not isinstance(value, str):
    raise DistutilsSetupError(
      f'virheellinen parametri: {attr}={value!r}'
    )

  # Poimi setup.py-tiedoston hakemisto.
  polku = os.path.dirname(value)

  # Lataa oletusparametrit `setup.cfg`-tiedostosta, jos on.
  parametrit = configparser.ConfigParser()
  parametrit.read(os.path.join(polku, 'setup.cfg'))

  # Alusta versiointiolio ja aseta se jakelun tietoihin.
  try:
    dist.git_versiointi = Versiointi(polku, **(
      parametrit['versiointi'] if parametrit.has_section('versiointi') else {}
    ))
  except ValueError:
    raise DistutilsSetupError(
      f'git-tietovarastoa ei löydy hakemistosta {polku!r}'
    )
    # except ValueError

  # def tarkista_git_versiointi


def finalize_distribution_options(dist):
  # pylint: disable=protected-access
  if dist.version != 0:
    return
  elif getattr(dist, 'git_versiointi', None) is not None:
    pass
  else:
    return

  # Näytä pyydettäessä tulosteena paketin versiotiedot.
  # Paluuarvona saadaan komentoriviltä määritetty revisio.
  pyydetty_ref = kasittele_parametrit(dist.git_versiointi)

  # Aseta versionumero ja git-historia.
  dist.metadata.version = dist.git_versiointi.versionumero(ref=pyydetty_ref)
  dist.historia = dist.git_versiointi.historia(ref=pyydetty_ref)

  # Aseta versiointi tiedostokohtaisen versioinnin määreeksi.
  _build_py.build_py.git_versiointi = dist.git_versiointi

  # def finalize_distribution_options

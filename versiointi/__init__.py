# -*- coding: utf-8 -*-

import configparser
import functools
import os
import re
import sys

from distutils.errors import DistutilsSetupError
from setuptools.command import build_py as _build_py

from .oletus import VERSIOKAYTANTO
from .parametrit import Distribution
from .tiedostot import build_py
from .vaatimukset import asennusvaatimukset


PKG_INFO_VERSIO = re.compile(r'Version\s*:\s*(.+)')


# Puukota `build_py`-komento huomioimaan tiedostokohtaiset
# versiointimääritykset.
_build_py.build_py = functools.wraps(_build_py.build_py, updated=())(
  type(_build_py.build_py)('build_py', (build_py, _build_py.build_py), {})
)


def asennustiedot(setup_py):
  ''' Vanha käyttötapa: `install_requires`-parametri. '''
  import warnings
  from setuptools import SetuptoolsDeprecationWarning
  warnings.warn(
    'asennustiedot()-mekanismi on vanhentunut.',
    SetuptoolsDeprecationWarning,
    stacklevel=2,
  )
  requirements = asennusvaatimukset(setup_py)
  return {
    **({'install_requires': requirements} if requirements else {})
  }
  # def asennustiedot


def _versionumero(setup_py):
  ''' Sisäinen käyttö: palauta pelkkä versionumero. '''
  dist = Distribution()
  try:
    tarkista_git_versiointi(dist, 'git_versiointi', setup_py)
    return dist.git_versiointi.versionumero(ref=dist.git_ref)
  except:
    return None
  # def _versionumero


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
    dist.git_versiointi = Versiointi(
      polku,
      kaytanto=(
        parametrit['versiointi']
        if 'versiointi' in parametrit
        else VERSIOKAYTANTO
      )
    )
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
    try:
      tarkista_git_versiointi(dist, 'git_versiointi', sys.argv[0])
    except (ModuleNotFoundError, DistutilsSetupError):
      dist.git_versiointi = None

  # Aseta jakelun tyyppi; tarvitaan komentoriviparametrien lisäämiseksi.
  dist.__class__ = Distribution

  if dist.git_versiointi is not None:
    # Aseta versionumero ja historia Git-tietojen perusteella.
    dist.metadata.version = dist.git_versiointi.versionumero(ref=dist.git_ref)
    dist.historia = dist.git_versiointi.historia(ref=dist.git_ref)

    # Aseta versiointi tiedostokohtaisen versioinnin määreeksi.
    _build_py.build_py.git_versiointi = dist.git_versiointi

  else:
    # Yritetään hakea versiotieto `sdist`-tyyppisen paketin PKG-INFOsta.
    try:
      with open(os.path.join(
        os.path.dirname(sys.argv[0]),
        'PKG-INFO'
      )) as pkg_info:
        for rivi in pkg_info:
          tulos = PKG_INFO_VERSIO.match(rivi)
          if tulos:
            dist.metadata.version = tulos.group(1)
            break
    except FileNotFoundError:
      pass
    # else (dist.git_versiointi is None)

  # def finalize_distribution_options


# Määrätään yo. funktio ajettavaksi myöhemmin kuin (mm.)
# `setuptools.dist:Distribution._finalize_setup_keywords`,
# sillä se olettaa, että setup-parametrit on jo prosessoitu.
finalize_distribution_options.order = 1

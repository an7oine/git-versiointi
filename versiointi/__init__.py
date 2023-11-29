# -*- coding: utf-8 -*-

import configparser
import functools
import logging
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


# Ohitetaan DEBUG-loki, sillä tämä sisältää mm. `git.cmd`-viestin jokaisesta
# GitPythonin ajamasta git-komennosta (subprocess.Popen).
logging.root.setLevel(logging.INFO)


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


def _versiointi(setup_py):
  ''' Muodosta versiointiolio setup.py-tiedoston sijainnin mukaan. '''
  from .versiointi import Versiointi

  # Poimi setup.py-tiedoston hakemisto.
  polku = os.path.dirname(setup_py)

  # Lataa oletusparametrit `setup.cfg`-tiedostosta, jos on.
  parametrit = configparser.ConfigParser()
  parametrit.read(os.path.join(polku, 'setup.cfg'))

  # Palauta versiointiolio.
  return Versiointi(
    polku,
    kaytanto=(
      parametrit['versiointi']
      if 'versiointi' in parametrit
      else VERSIOKAYTANTO
    )
  )
  # def _versiointi


def _poimi_sdist_versio(setup_py):
  ''' Poimi `sdist`-pakettiin tallennettu versionumero. '''
  with open(os.path.join(
    os.path.dirname(setup_py),
    'PKG-INFO'
  )) as pkg_info:
    for rivi in pkg_info:
      tulos = PKG_INFO_VERSIO.match(rivi)
      if tulos:
        return tulos.group(1)
  return None
  # def _poimi_sdist_versio


def _versionumero(setup_py):
  ''' Sisäinen käyttö: palauta pelkkä versionumero. '''
  try:
    dist = Distribution(attrs={'git_versiointi': setup_py})
  except DistutilsSetupError:
    return _poimi_sdist_versio(setup_py)
  else:
    return _versiointi(setup_py).versionumero(ref=dist.git_ref)
  # def _versionumero


def tarkista_git_versiointi(dist, attr, value):
  '''
  Sisääntulopiste setup-komentosarjalle silloin, kun parametri
  `setup_requires='git-versiointi'` on määritetty.

  Huomaa, että `attr` on aina `git_versiointi`. Arvo
  `value` on git-jakelun juurihakemisto.

  Versiointiolio muodostetaan git-tietojen perusteella ja
  asetetaan `dist.git_versiointi`-määreeseen.
  '''
  # pylint: disable=unused-argument, protected-access
  from .versiointi import Versiointi

  if isinstance(value, Versiointi):
    # Hyväksytään aiemmin asetettu versiointiolio (tupla-ajo).
    dist.git_versiointi = value
  elif not isinstance(value, str):
    raise DistutilsSetupError(
      f'virheellinen parametri: {attr}={value!r}'
    )
  else:
    # Alusta versiointiolio ja aseta se jakelun tietoihin.
    try:
      dist.git_versiointi = _versiointi(value)
    except ValueError:
      raise DistutilsSetupError(
        f'git-tietovarastoa ei löydy hakemistosta {value!r}'
      )
  return value
  # def tarkista_git_versiointi


def finalize_distribution_options(dist):
  '''
  Viimeistelyfunktio jakelun tietojen asettamisen jälkeen.

  – Puukotetaan setuptools-jakelun tyyppi, jotta voidaan käyttää
  tämän paketin tarjoamia laajennettuja komentoriviparametrejä.
  – Asetetaan paketin versionumero ja -historia git-tietovaraston
    mukaisesti.
  – Tallennetaan versiointiolio tiedostokohtaista versiointia varten.
  – Viimekätisenä ratkaisuna (git-tietovarastoa ei löytynyt)
    poimitaan pelkkä versionumero `sdist`-jakelun metatiedoista.
  '''
  # pylint: disable=protected-access
  from .versiointi import Versiointi

  if dist.version != 0:
    return

  asetettu_versiointi = getattr(dist, 'git_versiointi', None)
  if isinstance(asetettu_versiointi, Versiointi):
    pass
  else:
    try:
      dist.git_versiointi = _versiointi(
        asetettu_versiointi or sys.argv[0]
      )
    except:
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
      dist.metadata.version = _poimi_sdist_versio(
        sys.argv[0],
      )
    except FileNotFoundError:
      pass
    # else (dist.git_versiointi is None)

  # def finalize_distribution_options


# Määrätään yo. funktio ajettavaksi myöhemmin kuin (mm.)
# `setuptools.dist:Distribution._finalize_setup_keywords`,
# sillä se olettaa, että setup-parametrit on jo prosessoitu.
finalize_distribution_options.order = 1

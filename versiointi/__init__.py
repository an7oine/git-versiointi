# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, deprecated-module, wrong-import-position

import logging
from pathlib import Path
import re
import sys

if sys.version_info >= (3, 12):
  # Tarvitaan, jotta `import distutils` toimii.
  import setuptools.dist

from distutils.errors import DistutilsSetupError

from .asetukset import versiokaytanto
from .parametrit import Distribution
from .tiedostot import build_py, sdist


PKG_INFO_VERSIO = re.compile(r'Version\s*:\s*(.+)')


# Ohitetaan DEBUG-loki, sillä tämä sisältää mm. `git.cmd`-viestin jokaisesta
# GitPythonin ajamasta git-komennosta (subprocess.Popen).
logging.root.setLevel(logging.INFO)


def _versiointi(hakemisto: Path):
  ''' Muodosta versiointiolio annetun hakemiston mukaan. '''
  from .versiointi import Versiointi
  return Versiointi(
    hakemisto,
    kaytanto=versiokaytanto(hakemisto)
  )
  # def _versiointi


def _poimi_sdist_versio(hakemisto: Path):
  ''' Poimi `sdist`-pakettiin tallennettu versionumero. '''
  with open(hakemisto / 'PKG-INFO') as pkg_info:
    for rivi in pkg_info:
      tulos = PKG_INFO_VERSIO.match(rivi)
      if tulos:
        return tulos.group(1)
  return None
  # def _poimi_sdist_versio


def _versionumero(tiedosto: str):
  ''' Sisäinen käyttö: palauta pelkkä versionumero. '''
  hakemisto: Path = Path(tiedosto).parent
  try:
    dist = Distribution(attrs={'git_versiointi': hakemisto})
  except DistutilsSetupError:
    pass
  else:
    try:
      return _versiointi(hakemisto).versionumero(ref=dist.git_ref)
    except ValueError:
      pass

  return _poimi_sdist_versio(hakemisto)
  # def _versionumero


def tarkista_git_versiointi(dist, attr, value):
  '''
  Lue sisään (automaattisesti asetettu) parametri setup(git_versiointi=...).

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
    return value
  elif isinstance(value, str):
    value = Path(value)
  elif not isinstance(value, Path):
    raise DistutilsSetupError(
      f'virheellinen parametri: {attr}={value!r}'
    )
  # Alusta versiointiolio ja aseta se jakelun tietoihin.
  try:
    dist.git_versiointi = _versiointi(value)
  except ValueError as exc:
    raise DistutilsSetupError(
      f'git-tietovarastoa ei löydy hakemistosta {value!r}'
    ) from exc
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

  # Haetaan asennettavan paketin oma sijainti.
  # Kutsuttaessa `setup.py`-tiedostoa suoraan tämä on `sys.argv[0]` ja
  # paketin sijainti sen isäntähakemisto.
  # Muutoin (pyproject.toml, esim. `python -m build`) käytetään nykyistä
  # työhakemistoa, joka osoittaa PEP 517:n mukaan paketin lähdekoodiin.
  paketti = (
    setup_py.parent
    if sys.argv and (setup_py := Path(sys.argv[0])).name == 'setup.py'
    else Path.cwd()
  )
  asetettu_versiointi = getattr(dist, 'git_versiointi', None) or paketti

  if not isinstance(asetettu_versiointi, Versiointi):
    try:
      dist.git_versiointi = _versiointi(asetettu_versiointi)
    except Exception:
      dist.git_versiointi = None

  # Aseta jakelun tyyppi; tarvitaan komentoriviparametrien lisäämiseksi.
  dist.__class__ = Distribution

  if dist.git_versiointi is not None:
    # Aseta versionumero ja historia Git-tietojen perusteella.
    dist.metadata.version = dist.git_versiointi.versionumero(ref=dist.git_ref)
    dist.historia = dist.git_versiointi.historia(ref=dist.git_ref)

    # Puukotetaan `setuptools`-asennuskomentoja tarvittaessa
    # siten, että tiedostokohtaiset versioinnit huomioidaan
    # `sdist`-pakettia muodostettaessa.

    # Setup.py-pohjainen asennus: komento `build_py`.
    if not (o_build_py := dist.cmdclass.get('build_py')):
      from setuptools.command.build_py import build_py as o_build_py
    if not issubclass(o_build_py, build_py):
      class _build_py(build_py, o_build_py):
        git_versiointi = dist.git_versiointi
      dist.cmdclass['build_py'] = _build_py
      # elif not issubclass

    # PEP 517 -pohjainen asennus: komento `sdist`.
    if not (o_sdist := dist.cmdclass.get('sdist')):
      from setuptools.command.sdist import sdist as o_sdist
    if not issubclass(o_sdist, sdist):
      class _sdist(sdist, o_sdist):
        git_versiointi = dist.git_versiointi
      dist.cmdclass['sdist'] = _sdist
      # elif not issubclass

    # if dist.git_versiointi is not None

  else:
    # Yritetään hakea versiotieto `sdist`-tyyppisen paketin PKG-INFOsta.
    assert isinstance(asetettu_versiointi, Path)
    try:
      dist.metadata.version = _poimi_sdist_versio(asetettu_versiointi)
    except FileNotFoundError:
      pass
    # else (dist.git_versiointi is None)

  # def finalize_distribution_options


# Määrätään yo. funktio ajettavaksi myöhemmin kuin (mm.)
# `setuptools.dist:Distribution._finalize_setup_keywords`,
# sillä se olettaa, että setup-parametrit on jo prosessoitu.
finalize_distribution_options.order = 1

# -*- coding: utf-8 -*-

import configparser
from datetime import datetime
import os
import re
import sys
import warnings

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
  '''
  import distutils

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

  # Alusta versiointiolio.
  versiointi = Versiointi(polku, **kwargs)

  # Poimi mahdollinen `--ref`-parametri komentoriviltä.
  try:
    ref_i = sys.argv.index('--ref', 0, -1)
  except ValueError:
    ref = None
  else:
    ref = sys.argv[ref_i + 1]
    sys.argv[ref_i:ref_i+2] = []

  # Poimi ja tulosta annettuun versioon liittyvä
  # git-revisio `--ref`-parametrillä.
  oletus_hdo = distutils.dist.Distribution.handle_display_options
  def handle_display_options(self, option_order):
    option_order_muutettu = []
    muutettu = False
    for (opt, val) in option_order:
      if opt == 'ref':
        revisio = versiointi.revisio(val, ref=ref)
        if revisio is None:
          # pylint: disable=no-member
          raise distutils.errors.DistutilsOptionError(
            f'versiota {val} vastaavaa git-revisiota ei löydy'
          )
        print(revisio)
        muutettu = True
      else:
        option_order_muutettu.append((opt, val))
    return oletus_hdo(
      self, option_order_muutettu if muutettu else option_order
    ) or muutettu
    # def handle_display_options
  distutils.dist.Distribution.handle_display_options = handle_display_options
  distutils.dist.Distribution.display_options += [
    ('ref=', None, 'tulosta annettua versiota vastaava git-revisio')
  ]

  # Muodosta versionumero ja git-historia.
  try:
    param.update(dict(
      version=versiointi.versionumero(ref=ref),
      historia=versiointi.historia(ref=ref),
    ))
  except ValueError:
    warnings.warn('git-tietovarastoa ei löytynyt', RuntimeWarning)
    param['version'] = datetime.now().strftime('%Y%m%d.%H%M%s')
  return param
  # def asennustiedot

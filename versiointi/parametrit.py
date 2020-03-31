# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import distutils
import itertools
import sys


def kasittele_parametrit(versiointi):
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
      if opt == 'revisio':
        revisio = versiointi.revisio(val, ref=ref)
        if revisio is None:
          # pylint: disable=no-member
          raise distutils.errors.DistutilsOptionError(
            f'versiota {val} vastaavaa git-revisiota ei löydy'
          )
        print(revisio)
        muutettu = True
      elif opt == 'historia':
        for versio in itertools.islice(
          versiointi.historia(ref=ref), 0, int(val)
        ):
          print(versio)
        muutettu = True
      else:
        option_order_muutettu.append((opt, val))
    return oletus_hdo(
      self, option_order_muutettu if muutettu else option_order
    ) or muutettu
    # def handle_display_options

  distutils.dist.Distribution.handle_display_options = handle_display_options
  distutils.dist.Distribution.display_options += [
    ('historia=', None, 'tulosta annetun pituinen versiohistoria'),
    ('revisio=', None, 'tulosta annettua versiota vastaava git-revisio'),
  ]

  # Palautetaan mahdollinen vivun avulla määritetty git-revisio.
  return ref
  # def kasittele_parametrit

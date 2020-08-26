# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from distutils.errors import DistutilsOptionError
import functools
import itertools
import sys

from setuptools import dist


@functools.wraps(dist.Distribution, updated=())
class Distribution(dist.Distribution):
  display_options = dist.Distribution.display_options + [
    ('ref', None, 'tarkastele nimettyä git-revisiota'),
    ('historia=', None, 'tulosta annetun pituinen versiohistoria'),
    ('revisio=', None, 'tulosta annettua versiota vastaava git-revisio'),
  ]

  git_versiointi = None

  # Poimi mahdollinen komentorivillä annettu revisio.
  try:
    ref_i = sys.argv.index('--ref', 0, -1)
  except ValueError:
    git_ref = None
  else:
    git_ref, sys.argv[ref_i:ref_i + 2] = sys.argv[ref_i + 1], []

  def handle_display_options(self, option_order):
    if self.git_versiointi is None:
      return super().handle_display_options(option_order)

    option_order_muutettu = []
    muutettu = False
    for (opt, val) in option_order:
      if opt == 'ref':
        muutettu = True
      elif opt == 'revisio':
        revisio = self.git_versiointi.revisio(val, ref=self.git_ref)
        if revisio is None:
          # pylint: disable=no-member
          raise DistutilsOptionError(
            f'versiota {val} vastaavaa git-revisiota ei löydy'
          )
        print(revisio)
        muutettu = True
      elif opt == 'historia':
        for versio in itertools.islice(
          self.git_versiointi.historia(ref=self.git_ref), 0, int(val)
        ):
          print(versio)
        muutettu = True
      else:
        option_order_muutettu.append((opt, val))
    return super().handle_display_options(
      option_order_muutettu if muutettu else option_order
    ) or muutettu
    # def handle_display_options
  # class Distribution

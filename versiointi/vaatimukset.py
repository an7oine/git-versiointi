# -*- coding: utf-8 -*-

import os
import re


def asennusvaatimukset(setup_py):
  '''
  Palauta mahdolliset `requirements.txt`-tiedostossa
  määritellyt asennusvaatimukset.
  '''
  requirements_txt = os.path.join(
    os.path.dirname(setup_py), 'requirements.txt'
  )
  return [
    # Poimi muut kuin tyhjät ja kommenttirivit.
    # Lisää git-pakettirivin alkuun paketin nimi.
    re.sub(
      r'^(git\+(ssh|https).*/([^/.@]+)(\.git).*)$',
      r'\3 @ \1',
      rivi,
    )
    for rivi in map(str.strip, open(requirements_txt))
    if rivi and not rivi.startswith('#')
  ] if os.path.isfile(requirements_txt) else []
  # def asennusvaatimukset

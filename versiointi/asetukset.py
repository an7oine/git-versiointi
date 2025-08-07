from pathlib import Path
import sys

from .oletus import KAYTANTO, REF, VERSIOKAYTANTO


def toml_kaytanto(pyproject_toml: Path):
  '''
  Poimi `pyproject.toml`-asetuksista mahdollinen `[tool.versiointi]`-taulu
  ja muodosta sen mukainen versiointikäytäntö.
  '''
  if sys.version_info >= (3, 11):
    from tomllib import loads
  else:
    from tomli import loads
  try:
    pyproject = loads(
      pyproject_toml.read_text(encoding='utf-8')
    )
  except FileNotFoundError:
    return None
  try:
    versiointi = pyproject['tool']['versiointi']
  except KeyError:
    return None

  # Mikäli mitään ei määritelty ([tool.versiointi] on tyhjä),
  # käytetään oletuskäytäntöä.
  if not versiointi:
    return None

  # Mikäli asetukset on määritetty käsin:
  # - poimitaan mahdollinen "tunnettu" tai käsin määritelty
  #   käytäntö,
  # - muokataan tätä pyydetyiltä osin.
  if kaytanto := versiointi.pop('kaytanto', False):
    if isinstance(kaytanto, str):
      try:
        kaytanto = VERSIOKAYTANTO[kaytanto]
      except KeyError as exc:
        raise KeyError('Tuntematon vakiokäytäntö %r!' % kaytanto) from exc
    elif not isinstance(kaytanto, (list, dict)):
      raise ValueError(
        'Sopimaton käytäntö %r!' % kaytanto
      )
    elif kaytanto:
      kaytanto = {
        REF.get(avain, avain): KAYTANTO.get(arvo, arvo)
        for avain, arvo in dict(kaytanto).items()
      }
      if not all(isinstance(arvo, str) for arvo in kaytanto.values()):
        raise ValueError(
          'Sopimaton käytäntö %r!' % kaytanto
        )
      return kaytanto
    # if kaytanto := versiointi.get

  else:
    kaytanto = VERSIOKAYTANTO['oletus']

  if haara := dict(versiointi.pop('haara', {})):
    # Poistetaan vakiokäytännön avaimet `haara` ja `master_tai_vx`.
    # Lisätään tilalle luetellut avainparit.
    kaytanto = list(kaytanto.items())
    kaytanto[1:3] = []
    for avain, arvo in reversed(haara.items()):
      kaytanto[1:1] = [[REF.get(avain, avain), KAYTANTO.get(arvo, arvo)]]
    kaytanto = dict(kaytanto)

  if leima := dict(versiointi.pop('leima', {})):
    # Poistetaan vakiokäytännön avaimet `leima_kehitys` ja `leima`.
    # Lisätään tilalle luetellut avainparit.
    kaytanto = list(kaytanto.items())
    kaytanto[-3:-1] = []
    for avain, arvo in leima.items():
      kaytanto[-1:-1] = [[REF.get(avain, avain), KAYTANTO.get(arvo, arvo)]]
    kaytanto = dict(kaytanto)

  if muokattu := dict(versiointi.pop('muokattu', {})):
    # Korvataan kukin annettu avain annetulla arvolla.
    for avain, arvo in muokattu.items():
      kaytanto[REF.get(avain, avain)] = KAYTANTO.get(arvo, arvo)

  if versiointi:
    raise ValueError('Tuntematon asetus: %r!' % versiointi.join(', '))

  return kaytanto
  # def toml_kaytanto


def cfg_kaytanto(setup_cfg: Path):
  ''' Vanha määritys: [versiointi] määrittelee suoraan käytännön. '''
  import configparser
  setup = configparser.ConfigParser()
  try:
    setup.read(setup_cfg)
  except FileNotFoundError:
    return None
  try:
    return setup['versiointi']
  except KeyError:
    return None
  # def cfg_kaytanto


def versiokaytanto(hakemisto: Path):
  kaytanto = (
    toml_kaytanto(hakemisto / 'pyproject.toml')
    or cfg_kaytanto(hakemisto / 'setup.cfg')
    or VERSIOKAYTANTO['oletus']
  )
  if isinstance(kaytanto, list):
    return dict(kaytanto)
  else:
    return kaytanto
  # def versiokaytanto

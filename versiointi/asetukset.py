from pathlib import Path
import sys


def toml_asetukset(pyproject_toml: Path):
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
    return pyproject['tool']['versiointi']['kaytanto']
  except KeyError:
    return None
  # def toml_asetukset


def cfg_asetukset(setup_cfg: Path):
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
  # def cfg_asetukset


def versiokaytanto(hakemisto: Path):
  from .oletus import VERSIOKAYTANTO
  kaytanto = (
    toml_asetukset(hakemisto / 'pyproject.toml')
    or cfg_asetukset(hakemisto / 'setup.cfg')
    or VERSIOKAYTANTO
  )
  if isinstance(kaytanto, list):
    return dict(kaytanto)
  else:
    return kaytanto

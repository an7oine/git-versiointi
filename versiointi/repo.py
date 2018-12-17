# -*- coding: utf-8 -*-

from git.exc import InvalidGitRepositoryError
from git import Repo


def _muotoile_versio(leima, etaisyys):
  '''
  Poista löytyneen leiman alusta merkit `Vv-_.`
  ja lisää mahdollinen git-muutoshistorian pituus aliversiona.
  '''
  return (
    str(leima).lstrip('Vv-_.') if leima else '0.0'
  ) + (
    f'.{etaisyys}' if etaisyys else ''
  )
  # def _muotoile_versio


def git_historia(polku):
  '''
  Muodosta versiohistoria git-tietovaraston sisällön mukaan.
  Args:
    polku (str): `.git`-alihakemiston sisältävä polku
  Yields:
    muutos (tuple): versio ja viesti, uusin ensin, esim.
      ``('1.0.2', 'Lisätty uusi toiminnallisuus Y')``,
      ``('1.0.1', 'Lisätty uusi toiminnallisuus X')``, ...
  '''
  try:
    repo = Repo(polku)
  except InvalidGitRepositoryError:
    raise ValueError(f'Virheellinen polku: {polku}')

  def muutokset():
    yield repo.head.commit
    yield from repo.head.commit.iter_parents()

  leima, etaisyys = None, 0
  for ref in muutokset():
    etaisyys -= 1

    # Jos aiemmin löydetty leima on edelleen käytettävissä,
    # muodosta versionumero sen perusteella.
    if etaisyys > 0:
      yield {
        'tyyppi': 'muutos',
        'tunnus': ref.hexsha,
        'versio': _muotoile_versio(leima, etaisyys),
        'kuvaus': ref.message.rstrip('\n'),
      }
      continue
      # if etaisyys >= 0

    # Jos tälle viittaukselle on suora leima, käytä sitä.
    leima = repo.git.tag('--points-at', ref.hexsha)
    if leima:
      yield {
        'tyyppi': 'julkaisu',
        'tunnus': repo.tags[leima].object.hexsha,
        'versio': _muotoile_versio(leima, 0),
        'kuvaus': getattr(repo.tags[leima].tag, 'message', '').rstrip('\n'),
      }
      yield {
        'tyyppi': 'muutos',
        'tunnus': ref.hexsha,
        'versio': _muotoile_versio(leima, 0),
        'kuvaus': ref.message.rstrip('\n'),
      }

    else:
      # Etsi lähin leima.
      etaisyys = 1
      for aiempi_ref in ref.iter_parents():
        leima = repo.git.tag('--points-at', aiempi_ref.hexsha)
        if leima:
          yield {
            'tyyppi': 'muutos',
            'tunnus': ref.hexsha,
            'versio': _muotoile_versio(leima, etaisyys),
            'kuvaus': ref.message.rstrip('\n'),
          }
          break
        etaisyys += 1
        # for aiempi_ref

      if not leima:
        # Jos yhtään leimaa ei löytynyt, palauta git-historian pituus.
        yield {
          'tyyppi': 'muutos',
          'tunnus': ref.hexsha,
          'versio': _muotoile_versio(None, etaisyys),
          'kuvaus': ref.message.rstrip('\n'),
        }
    # for ref
  # def git_historia


def git_versio(polku):
  '''
  Muodosta versionumero git-tietovaraston leimojen mukaan.
  Args:
    polku (str): `.git`-alihakemiston sisältävä polku
  Returns:
    versionumero (str): esim. '1.0.2'
  '''
  try:
    repo = Repo(polku)
  except InvalidGitRepositoryError:
    raise ValueError(f'Virheellinen polku: {polku}')

  # Aloita HEAD-viittauksesta.
  try:
    ref = repo.head.commit
  except ValueError:
    return '0'

  # Jos HEAD osoittaa suoraan johonkin leimaan, palauta se.
  leima = repo.git.tag('--points-at', ref.hexsha)
  if leima:
    return _muotoile_versio(leima, 0)

  # Etsi lähin leima ja palauta `leima.n`, missä `n` on etäisyys.
  etaisyys = 1
  for ref in ref.iter_parents():
    leima = repo.git.tag('--points-at', ref.hexsha)
    if leima:
      return _muotoile_versio(leima, etaisyys)
    etaisyys += 1

  # Jos yhtään leimaa ei löytynyt, palauta git-historian pituus.
  return _muotoile_versio(None, etaisyys)
  # def git_versio

# -*- coding: utf-8 -*-

import pkg_resources
import re

from git.exc import InvalidGitRepositoryError
from git.objects.commit import Commit
from git.objects.tag import TagObject
from git import Repo

VERSIO = re.compile(r'^v[0-9]', flags=re.IGNORECASE)
KEHITYSVERSIO = re.compile(r'(.+[a-z])([0-9]*)$', flags=re.IGNORECASE)


def _normalisoi(versio):
  try:
    return str(pkg_resources.packaging.version.Version(versio))
  except pkg_resources.packaging.version.InvalidVersion:
    return versio


def _muotoile_versio(leima, etaisyys, versio=None, aliversio=None):
  '''
  Määritä versionumero käytännön mukaisesti versiolle, kehitysversiolle ja aliversiolle.

  Args:
    leima (git.Tag): lähin git-leima (tag)
    etaisyys (int): muutosten lukumäärä leiman jälkeen
    versio (callable / str): version numerointi, oletus `"{leima}"`
    aliversio (callable / str): aliversion numerointi, oletus `"{leima}.{etaisyys}"`
  '''
  if leima is not None:
    kehitysversio = KEHITYSVERSIO.match(str(leima))
    if kehitysversio:
      if kehitysversio.group(2):
        etaisyys += int(kehitysversio.group(2))
      return _normalisoi(f'{kehitysversio.group(1)}{etaisyys}')

  if not callable(versio):
    assert not versio or isinstance(versio, str)
    versio = (versio or '{leima}').format
  if not callable(aliversio):
    assert not aliversio or isinstance(aliversio, str)
    aliversio = (aliversio or '{leima}.{etaisyys}').format

  return _normalisoi((aliversio if etaisyys else versio)(
    leima=leima or 'v0.0',
    etaisyys=etaisyys,
  ))
  # def _muotoile_versio


def git_muutos(repo, ref):
  '''
  Etsitään ja palautetaan annetun git-objektin osoittama muutos (git-commit).
  '''
  if isinstance(ref, Commit):
    return ref
  elif isinstance(ref, TagObject):
    return git_muutos(repo, ref.object)
  else:
    return git_muutos(repo, ref.commit)
  # def git_muutos


def git_leima(repo, ref, kehitysversio=False):
  '''
  Etsitään ja palautetaan versiojärjestyksessä viimeisin viittaukseen osoittava leima.
  Ohita kehitysversiot, ellei toisin pyydetä.
  '''
  if kehitysversio:
    suodatin = lambda l: l.commit == ref and VERSIO.match(str(l))
  else:
    suodatin = lambda l: (
      l.commit == ref and VERSIO.match(str(l)) and not KEHITYSVERSIO.match(str(l))
    )
  try:
    return next(iter(sorted(
      filter(suodatin, repo.tags),
      key=lambda x: pkg_resources.parse_version(str(x)),
      reverse=True,
    )))
  except StopIteration:
    return None
  # def git_leima


def git_historia(polku, ref=None, versio=None, aliversio=None):
  '''
  Muodosta versiohistoria git-tietovaraston sisällön mukaan.
  Args:
    polku (str): `.git`-alihakemiston sisältävä polku
    ref (str): git-viittaus (oletus HEAD)
    versio (str): version numerointi
    aliversio (str): aliversion numerointi
  Yields:
    muutos (tuple): versio ja viesti, uusin ensin, esim.
      ``('1.0.2', 'Lisätty uusi toiminnallisuus Y')``,
      ``('1.0.1', 'Lisätty uusi toiminnallisuus X')``, ...
  '''
  try:
    repo = Repo(polku)
  except InvalidGitRepositoryError:
    raise ValueError(f'Virheellinen polku: {polku}')

  # Aloita annetusta viittauksesta tai HEAD-osoittimesta.
  try:
    aloitus_ref = (
      git_muutos(repo, repo.rev_parse(ref)) if ref
      else repo.head.commit
    )
  except ValueError:
    return

  def muutokset():
    yield aloitus_ref
    yield from aloitus_ref.iter_parents()

  leima, etaisyys = None, 0
  for ref in muutokset():
    etaisyys -= 1

    # Jos aiemmin löydetty leima on edelleen viimeisin löytynyt,
    # muodosta kehitys- tai aliversionumero sen perusteella.
    if etaisyys > 0:
      yield {
        'tyyppi': 'muutos',
        'tunnus': ref.hexsha,
        'versio': _muotoile_versio(
          leima=leima, etaisyys=etaisyys,
          versio=versio, aliversio=aliversio,
        ),
        'kuvaus': ref.message.rstrip('\n'),
      }
      continue
      # if etaisyys >= 0

    # Etsi mahdollinen julkaistu versiomerkintä ja lisää se
    # julkaisuna versiohistoriaan.
    julkaisuleima = git_leima(repo, ref, kehitysversio=False)
    if julkaisuleima:
      yield {
        'tyyppi': 'julkaisu',
        'tunnus': julkaisuleima.object.hexsha,
        'versio': _muotoile_versio(
          leima=julkaisuleima, etaisyys=0,
          versio=versio, aliversio=aliversio,
        ),
        'kuvaus': getattr(julkaisuleima.tag, 'message', '').rstrip('\n'),
      }
      leima = julkaisuleima
    # Muutoin ohitetaan julkaisumerkintä ja etsitään uudelleen kehitysversiota.
    else:
      julkaisuleima = None
      leima = git_leima(repo, ref, kehitysversio=True)

    # Jos kehitysversiomerkintä löytyi, lisää sellaisenaan.
    if leima:
      yield {
        'tyyppi': 'muutos',
        'tunnus': ref.hexsha,
        'versio': _muotoile_versio(
          leima=leima, etaisyys=0,
          versio=versio, aliversio=aliversio,
        ),
        'kuvaus': ref.message.rstrip('\n'),
      }

    # Etsi uudelleen mahdollista uudempaa kehitysversiomerkintää,
    # mikäli kyseessä on lopullinen, julkaistu versio.
    if julkaisuleima:
      leima = git_leima(repo, ref, kehitysversio=True)

    # Jos yhtään tähän muutokseen osoittavaa leimaa ei löytynyt,
    # etsi viimeisin, aiempi (kehitys-) versio ja luo aliversio sen mukaan.
    if not leima:
      # Etsi lähin leima.
      etaisyys = 1
      for aiempi_ref in ref.iter_parents():
        leima = git_leima(repo, aiempi_ref, kehitysversio=True)
        if leima:
          yield {
            'tyyppi': 'muutos',
            'tunnus': ref.hexsha,
            'versio': _muotoile_versio(
              leima=leima, etaisyys=etaisyys,
              versio=versio, aliversio=aliversio,
            ),
            'kuvaus': ref.message.rstrip('\n'),
          }
          break
        etaisyys += 1
        # for aiempi_ref

      # Jos myöskään yhtään aiempaa versiomerkintää ei löytynyt,
      # muodosta versionumero git-historian pituuden mukaan.
      if not leima:
        yield {
          'tyyppi': 'muutos',
          'tunnus': ref.hexsha,
          'versio': _muotoile_versio(
            leima=None, etaisyys=etaisyys,
            versio=versio, aliversio=aliversio,
          ),
          'kuvaus': ref.message.rstrip('\n'),
        }
    # for ref
  # def git_historia


def git_versio(polku, ref=None, versio=None, aliversio=None):
  '''
  Muodosta versionumero git-tietovaraston leimojen mukaan.
  Args:
    polku (str): `.git`-alihakemiston sisältävä polku
    ref (str): git-viittaus (oletus HEAD)
    versio (str): version numerointi
    aliversio (str): aliversion numerointi
  Returns:
    versionumero (str): esim. '1.0.2'
  '''
  try:
    repo = Repo(polku)
  except InvalidGitRepositoryError:
    raise ValueError(f'Virheellinen polku: {polku}')

  # Aloita annetusta viittauksesta tai HEAD-osoittimesta.
  try:
    ref = (
      git_muutos(repo, repo.rev_parse(ref)) if ref
      else repo.head.commit
    )
  except ValueError:
    return _normalisoi('v0')

  # Jos viittaus osoittaa suoraan johonkin julkaisuun, palauta se.
  leima = git_leima(repo, ref, kehitysversio=False)
  if leima:
    return _muotoile_versio(
      leima=leima, etaisyys=0,
      versio=versio, aliversio=aliversio,
    )

  # Jos viittaus osoittaa suoraan johonkin kehitysversioon, palauta se.
  leima = git_leima(repo, ref, kehitysversio=True)
  if leima:
    return _muotoile_versio(
      leima=leima, etaisyys=0,
      versio=versio, aliversio=aliversio,
    )

  # Etsi lähin leima ja palauta määritetyn käytännön mukainen aliversio:
  # oletuksena `leima.n`, missä `n` on etäisyys.
  etaisyys = 1
  for ref in ref.iter_parents():
    leima = git_leima(repo, ref, kehitysversio=True)
    if leima:
      return _muotoile_versio(
        leima=leima, etaisyys=etaisyys,
        versio=versio, aliversio=aliversio,
      )
    etaisyys += 1

  # Jos yhtään aiempaa versiomerkintää ei löytynyt,
  # muodosta versionumero git-historian pituuden mukaan.
  return _muotoile_versio(
    leima=None, etaisyys=etaisyys,
    versio=versio, aliversio=aliversio,
  )
  # def git_versio

# -*- coding: utf-8 -*-

import itertools

from pkg_resources import parse_version

from git.objects.commit import Commit
from git.objects.tag import TagObject
from git import Repo

from .oletus import VERSIO, KEHITYSVERSIO


class Tietovarasto(Repo):
  ''' Täydennetty git-tietovarastoluokka. '''

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    leimat = self.versioleimat = {}
    for leima in self.tags:
      if VERSIO.match(str(leima)):
        leimat.setdefault(leima.commit.binsha, []).append(leima)
    self.haarat = {}
    # def __init__

  def muutos(self, ref=None):
    '''
    Etsitään ja palautetaan annetun git-objektin osoittama muutos (git-commit).
    '''
    if ref is None:
      return self.head.commit
    elif isinstance(ref, str):
      ref = self.rev_parse(ref)
    if isinstance(ref, Commit):
      return ref
    elif isinstance(ref, TagObject):
      return self.muutos(ref.object)
    else:
      return self.muutos(ref.commit)
    # def muutos

  def haara(self, ref=None, tyyppi=None):
    '''
    Etsitään ja palautetaan se haara (esim 'ref/heads/master'),
    joka sisältää annetun git-revision ja täsmää annettuun tyyppiin
    (tai välilyönnillä erotettuihin tyyppeihin).

    Useista täsmäävistä haaroista palautetaan jokin satunnainen.

    Mikäli yhtään täsmäävää haaraa ei löydy, palautetaan None.

    Käytetään välimuistia
    '''
    ref = self.muutos(ref)
    try: return self.haarat[ref.binsha, tyyppi]
    except KeyError: pass
    haara = self.haarat[ref.binsha, tyyppi] = self.git.for_each_ref(
      '--count=1',
      '--format=%(refname)',
      '--contains', ref,
      *(tyyppi.split(' ') if tyyppi else ()),
    ) or None
    return haara
    # def haara

  def leima(self, ref=None, kehitysversio=False):
    '''
    Etsitään ja palautetaan versiojärjestyksessä viimeisin
    viittaukseen osoittava leima.
    Ohita kehitysversiot, ellei toisin pyydetä.
    '''
    versiot = self.versioleimat.get(self.muutos(ref).binsha, [])
    if not kehitysversio:
      versiot = filter(
        lambda l: not KEHITYSVERSIO.match(str(l)),
        versiot
      )
    try:
      return next(iter(sorted(
        versiot,
        key=lambda x: parse_version(str(x)),
        reverse=True,
      )))
    except StopIteration:
      return None
    # def leima

  def muutokset(self, ref=None):
    '''
    Tuota annettu revisio ja kaikki sen edeltäjät.
    '''
    ref = self.muutos(ref)
    return itertools.chain((ref, ), ref.iter_parents())
    # def muutokset

  def muutosloki(self, ref=None):
    '''
    Tuota git-tietovaraston muutosloki alkaen annetusta revisiosta.

    Args:
      polku (str): `.git`-alihakemiston sisältävä polku
      ref (str): git-viittaus (oletus HEAD)

    Yields:
      (ref, leima, etaisyys)
    '''
    leima, etaisyys = None, 0
    # pylint: disable=redefined-argument-from-local
    for ref in self.muutokset(ref):
      etaisyys -= 1

      # Jos aiemmin löydetty leima on edelleen viimeisin löytynyt,
      # muodosta kehitys- tai aliversionumero sen perusteella.
      if etaisyys > 0:
        yield ref, leima, etaisyys
        continue
        # if etaisyys >= 0

      # Etsi mahdollinen julkaistu versiomerkintä ja lisää se
      # julkaisuna versiohistoriaan.
      julkaisuleima = self.leima(ref, kehitysversio=False)
      if julkaisuleima:
        yield julkaisuleima.object, julkaisuleima, 0
        leima = julkaisuleima

      # Muutoin ohitetaan julkaisumerkintä
      # ja etsitään uudelleen kehitysversiota.
      else:
        julkaisuleima = None
        leima = self.leima(ref, kehitysversio=True)

      # Jos kehitysversiomerkintä löytyi, lisää sellaisenaan.
      if leima:
        yield ref, leima, 0

      # Etsi uudelleen mahdollista uudempaa kehitysversiomerkintää,
      # mikäli kyseessä on lopullinen, julkaistu versio.
      if julkaisuleima:
        leima = self.leima(ref, kehitysversio=True)

      # Jos yhtään tähän muutokseen osoittavaa leimaa ei löytynyt,
      # etsi viimeisin, aiempi (kehitys-) versio ja luo aliversio sen mukaan.
      if not leima:
        # Etsi lähin leima.
        etaisyys = 1
        for aiempi_ref in ref.iter_parents():
          leima = self.leima(aiempi_ref, kehitysversio=True)
          if leima:
            yield ref, leima, etaisyys
            break
          etaisyys += 1
          # for aiempi_ref

        # Jos myöskään yhtään aiempaa versiomerkintää ei löytynyt,
        # muodosta versionumero git-historian pituuden mukaan.
        if not leima:
          yield ref, leima, etaisyys
      # for ref
    # def muutosloki

  # class Tietovarasto

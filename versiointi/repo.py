# -*- coding: utf-8 -*-

import itertools
import re

import pkg_resources

from git.objects.commit import Commit
from git.objects.tag import TagObject
from git.refs.remote import RemoteReference
from git import Repo


class Tietovarasto(Repo):

  VERSIO = re.compile(r'^v[0-9]', flags=re.IGNORECASE)
  KEHITYSVERSIO = re.compile(r'(.+[a-z])([0-9]*)$', flags=re.IGNORECASE)

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    leimat = self.versioleimat = {}
    for l in self.tags:
      if self.VERSIO.match(str(l)):
        leimat.setdefault(l.commit.binsha, []).append(l)
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

  @property
  def vierashaarat(self):
    '''Tietovaraston vieraspään sisältämät haarat.

    Ohitetaan refs/remotes/origin/HEAD.
    '''
    return (
      haara
      for haara in RemoteReference.iter_items(self)
      if haara.is_detached
    )
    # def vierashaarat

  def leima(self, ref=None, kehitysversio=False):
    '''
    Etsitään ja palautetaan versiojärjestyksessä viimeisin
    viittaukseen osoittava leima.
    Ohita kehitysversiot, ellei toisin pyydetä.
    '''
    versiot = self.versioleimat.get(self.muutos(ref).binsha, [])
    if not kehitysversio:
      versiot = filter(
        lambda l: not self.KEHITYSVERSIO.match(str(l)),
        versiot
      )
    try:
      return next(iter(sorted(
        versiot,
        key=lambda x: pkg_resources.parse_version(str(x)),
        reverse=True,
      )))
    except StopIteration:
      return None
    # def leima

  def muutokset(self, ref=None):
    ref = self.muutos(ref)
    return itertools.chain((ref, ), ref.iter_parents())
    # def muutokset

  def oksa(self, ref=None):
    ref = self.muutos(ref)
    try:
      master, = self.merge_base('origin/master', ref)
    except: # pylint: disable=bare-except
      return None, None
    oksa = 0
    for muutos in self.muutokset(ref):
      if muutos == master:
        return master, oksa
      oksa += 1
    raise RuntimeError
    # def oksa

  def muutosloki(self, ref=None):
    '''
    Tuota git-tietovaraston muutosloki alkaen annetusta muutoksesta.

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

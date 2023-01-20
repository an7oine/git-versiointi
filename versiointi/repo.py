# -*- coding: utf-8 -*-

import itertools
import re

from pkg_resources import parse_version
from pkg_resources.extern.packaging.version import InvalidVersion

from git.objects.commit import Commit
from git.objects.tag import TagObject
from git import Git, Repo


class LiianVanha(Repo):
  def __init__(self, *args, **kwargs):
    raise RuntimeError(
      'Järjestelmän git-versio on liian vanha.'
      ' Git 1.7.10+ vaaditaan versioinnin käyttöön.'
    )
    # def __init__
  # class LiianVanha


class Repo1_7_10(Repo):
  ''' Toteutus symboleiden hakuun, git v.1.7.10+. '''
  def _symboli(self, ref, tyyppi):
    # Poimitaan erilliset, välilyönnein erotetut tyyppikriteerit.
    # Muodostetaan mahdollinen säännöllinen lauseke viimeisen tyypin
    # viimeisen kauttaviivan jälkeisen osan mukaan.
    tyypit = tyyppi.split(' ') if tyyppi else ()
    if tyypit and '/' in tyypit[-1]:
      lauseke = tyypit[-1].rsplit('/', 1)[-1]

    if tyyppi.startswith('refs/tags'):
      symbolit = self.git.tag('--points-at', ref).split('\n')
      symbolit = (f'refs/tags/{symboli}' for symboli in symbolit)
    else:
      symbolit = self.git.branch(
        '--contains', ref,
        '--all',
      ).split('\n')
      symbolit = (
        f'refs/{symboli[2:]}'
        if '/' in symboli
        else f'refs/heads/{symboli[2:]}'
        for symboli in symbolit
      )

    return filter(
      re.compile(rf'.*/{lauseke}$').match if lauseke else None,
      symbolit
    )
    # def _etsi_symboli
  # class Repo1_7_10


class Repo2_7_0(Repo):
  ''' Toteutus symboleiden hakuun, git v.2.7.0+. '''
  def _symboli(self, ref, tyyppi):
    # Poimitaan erilliset, välilyönnein erotetut tyyppikriteerit.
    # Muodostetaan mahdollinen säännöllinen lauseke viimeisen tyypin
    # viimeisen kauttaviivan jälkeisen osan mukaan.
    tyypit = tyyppi.split(' ') if tyyppi else ()
    if tyypit and '/' in tyypit[-1]:
      lauseke = tyypit[-1].rsplit('/', 1)[-1]
    else:
      lauseke = None

    return filter(
      re.compile(rf'.*/{lauseke}$').match if lauseke else None,
      self.git.for_each_ref(
        # Pyydetään tuloksena ainoastaan viittauksen nimi.
        '--format=%(refname)',

        # Huomaa, että haara viittaa (nimeämismielessä) paitsi tällä het-
        # kellä osoittamaansa muutokseen, myös kaikkiin tämän edeltäjiin.
        # Leima taas viittaa pysyvästi täsmälleen yhteen muutokseen.
        '--points-at'
        if tyyppi and tyyppi.startswith('refs/tags')
        else '--contains',
        ref,

        # Poimitaan alkuosa (viimeiseen kauttaviivaan saakka) kustakin
        # annetusta tyypistä.
        *(tyyppi.rsplit('/', 1)[0] for tyyppi in tyypit),
      ).split('\n')
    )
    # def _etsi_symboli
  # class Repo2_7_0


_git_versio = Git().version_info
class Tietovarasto(
  (
    Repo2_7_0 if _git_versio >= (2, 7, 0)
    else Repo1_7_10 if _git_versio >= (1, 7, 10)
    else LiianVanha
  ),
  Repo,
):
  ''' Täydennetty git-tietovarastoluokka. '''

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

  def symboli(self, ref=None, tyyppi=None):
    '''
    Etsitään ja palautetaan se symboli (esim 'ref/heads/master'),
    joka sisältää annetun git-revision ja täsmää annettuun tyyppiin
    (tai välilyönnillä erotettuihin tyyppeihin).

    Useista täsmäävistä symboleista palautetaan
    1. versiojärjestyksessä suurin kelvollinen versionumero; tai
    2. aakkosjärjestyksessä suurin.

    Mikäli yhtään täsmäävää symbolia ei löydy, palautetaan None.

    Käytetään revisio- ja tyyppikohtaista välimuistia.

    Huomaa, että `git-for-each-ref` käyttää `fnmatch(3)`-pohjaista
    kuviohakua. Tässä korvataan se pyydettyjen polkujen viimeisen
    osan osalta vertailulla säännölliseen lausekkeeseen.
    '''
    # pylint: disable=access-member-before-definition
    # pylint: disable=attribute-defined-outside-init
    ref = self.muutos(ref)
    try: return self.symbolit[ref.binsha, tyyppi]
    except AttributeError: self.symbolit = {}
    except KeyError: pass

    # Poimitaan pyydetyt symbolit Git-versiokohtaisen
    # toteutuksen mukaan.
    symbolit = self._symboli(ref, tyyppi)

    # Mikäli yhtään symbolia ei löytynyt, palautetaan `None`.
    # Mikäli löytyi yksi, palautetaan se.
    # Mikäli löytyi useampia, palautetaan versiojärjestyksessä suurin.
    # Löytynyt, tyhjä symboli korvataan `Nonella`.
    def jarjestys(symboli):
      try:
        return (True, parse_version(symboli), symboli)
      except InvalidVersion:
        return (False, None, symboli)
    try:
      symboli, *__ = sorted(
        symbolit,
        key=jarjestys,
        reverse=True,
      )
    except ValueError:
      symboli = None
    self.symbolit[ref.binsha, tyyppi] = symboli = (
      None if symboli is None else str(symboli)
    )
    return symboli
    # def symboli

  def muutokset(self, ref=None):
    '''
    Tuota annettu revisio ja kaikki sen edeltäjät.
    '''
    ref = self.muutos(ref)
    return itertools.chain((ref, ), ref.iter_parents())
    # def muutokset

  # class Tietovarasto

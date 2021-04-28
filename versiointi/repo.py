# -*- coding: utf-8 -*-

import itertools
import re

from pkg_resources import parse_version

from git.objects.commit import Commit
from git.objects.tag import TagObject
from git import Repo


class Tietovarasto(Repo):
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

    Useista täsmäävistä symboleista palautuu jokin satunnainen.

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

    # Poimitaan erilliset, välilyönnein erotetut tyyppikriteerit.
    # Muodostetaan mahdollinen säännöllinen lauseke viimeisen tyypin
    # viimeisen kauttaviivan jälkeisen osan mukaan.
    tyypit = tyyppi.split(' ') if tyyppi else ()
    if tyypit and '/' in tyypit[-1]:
      lauseke = tyypit[-1].rsplit('/', 1)[-1]

    symbolit = filter(
      re.compile(rf'.*/{lauseke}$').match if lauseke else None,
      self.git.for_each_ref(
        # Pyydetään tuloksena ainoastaan viittauksen nimi.
        '--format=%(refname)',

        # Huomaa, että haara viittaa (nimeämismielessä) paitsi tällä het-
        # kellä osoittamaansa muutokseen, myös kaikkiin tämän edeltäjiin.
        # Leima taas viittaa pysyvästi täsmälleen yhteen muutokseen.
        '--points-at' if tyyppi.startswith('refs/tags') else '--contains', ref,

        # Poimitaan alkuosa (viimeiseen kauttaviivaan saakka) kustakin
        # annetusta tyypistä.
        *(tyyppi.rsplit('/', 1)[0] for tyyppi in tyypit),
      ).split('\n')
    )

    # Mikäli yhtään symbolia ei löytynyt, palautetaan `None`.
    # Mikäli löytyi yksi, palautetaan se.
    # Mikäli löytyi useampia, palautetaan versiojärjestyksessä suurin.
    # Löytynyt, tyhjä symboli korvataan `Nonella`.
    try:
      symboli, *muut = symbolit
    except ValueError:
      symboli = None
    else:
      if muut:
        # Parsitaan symboli versionumeroksi vain tarvittaessa.
        symboli = parse_version(symboli)
        for muu_symboli in map(parse_version, muut):
          if muu_symboli > symboli:
            symboli = muu_symboli
        symboli = str(symboli)
        # if muut
      symboli = symboli or None
    self.symbolit[ref.binsha, tyyppi] = symboli
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

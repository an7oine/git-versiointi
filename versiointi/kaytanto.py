# -*- coding: utf-8 -*-

import itertools
import re

import pkg_resources


class KaytantoMeta(type):
  '''
  Yksittäisen versiointikäytännön tyyppi.
  '''
  def __new__(mcs, name, bases, attrs, *, i=None, tyyppi=None, kaytanto=None):
    # Muodosta yksilöllinen luokkanimi.
    if i is not None:
      name = f'{name}_{i}'
    # Tallenna tyyppi ja käytäntö luokkakohtaisiin määreisiin.
    return super().__new__(mcs, name, bases, {
      **attrs,
      f'_{name}__tyyppi': tyyppi,
      f'_{name}__kaytanto': staticmethod(kaytanto),
    })
    # def __new__

  # Huomaa, että metaluokan määreet ovat olioluokan luokkamääreitä.
  @property
  def _tyyppi(cls):
    return getattr(cls, f'_{cls.__name__}__tyyppi')

  @property
  def _kaytanto(cls):
    return getattr(cls, f'_{cls.__name__}__kaytanto')

  # class KaytantoMeta


class Kaytanto(metaclass=KaytantoMeta):
  def versio_indeksi_etaisyys(self, ref):
    '''
    Laskee versionumeron lähimmän käytäntöön täsmäävän git-revision
    kohdalla, mahdollisen indeksiosan sekä etäisyyden tähän revisioon.
    '''
    raise NotImplementedError
  # class Kaytanto


class Versiomuotoilu:
  def __init__(self, aihio):
    self.aihio = aihio
  def __call__(self, **kwargs):
    self.indeksoitu = False
    class MerkitseIndeksointi:
      def __str__(self2):
        self.indeksoitu = True
        return ''
    kwargs['indeksoitu'] = MerkitseIndeksointi()
    versio = eval(f"f'''{self.aihio}'''", kwargs)
    if self.indeksoitu:
      versio, indeksi = list(versio), []
      while versio and versio[-1].isdigit():
        indeksi[:0], versio[-1:] = versio[-1:], []
      return ''.join(versio), ''.join(indeksi)
    else:
      return versio, ''
    # def __call__
  # class Versiomuotoilu


class VersiointiMeta(KaytantoMeta):
  '''
  Versiointikäytäntöjen järjestelmän tyyppi.
  '''
  def __new__(mcs, name, bases, attrs, *, kaytanto):
    # pylint: disable=no-member, unused-variable, protected-access
    bases = list(bases)

    # Muodostetaan määritetyn käytännön mukaiset muotoilufunktioit.
    def muotoilija(aihio):
      # pylint: disable=eval-used
      return Versiomuotoilu(aihio)
      # def muotoilija

    # Poimitaan irto-, symboliset ja nollakäytäntö erikseen
    # versiointimäärityksen mukaan.
    (_, irtokaytanto), *symboliset_kaytannot, (_, nollakaytanto) = (
      (avain, muotoilija(arvo))
      for avain, arvo in kaytanto.items()
    )

    # Muodostetaan luokkahierarkia käytäntöjen mukaan.
    @bases.append
    class Irtoversio(Kaytanto, kaytanto=irtokaytanto):
      def versio_indeksi_etaisyys(self, ref):
        tyyppi, kaytanto = __class__._tyyppi, __class__._kaytanto
        pohja, indeksi, etaisyys = super().versio_indeksi_etaisyys(ref)
        if not etaisyys:
          return pohja, indeksi, etaisyys
        return *kaytanto(
          ref=ref,
          pohja=pohja,
          indeksi=indeksi,
          etaisyys=etaisyys
        ), 0
      # class Irtoversio

    for i, (tyyppi, symbolinen_kaytanto) in enumerate(symboliset_kaytannot):
      @bases.append
      class SymbolinenVersio(
        Kaytanto, i=i, tyyppi=tyyppi, kaytanto=symbolinen_kaytanto
      ):
        def versio_indeksi_etaisyys(self, ref):
          tyyppi, kaytanto = __class__._tyyppi, __class__._kaytanto
          pohja, indeksi, etaisyys = super().versio_indeksi_etaisyys(ref)
          for j, muutos in enumerate(itertools.islice(
            self.tietovarasto.muutokset(ref), etaisyys
          )):
            symboli = self.tietovarasto.symboli(muutos, tyyppi)
            if symboli is not None:
              return *kaytanto(
                ref=muutos,
                tunnus=symboli.split('/')[-1],
                pohja=pohja,
                indeksi=indeksi,
                etaisyys=etaisyys-j,
              ), j
            # for j, muutos
          return pohja, indeksi, etaisyys
          # def versio_indeksi_etaisyys
        # class SymbolinenVersio

    @bases.append
    class Nollaversio(Kaytanto, kaytanto=nollakaytanto):
      def versio_indeksi_etaisyys(self, ref):
        return (
          *__class__._kaytanto(),
          len(list(self.tietovarasto.muutokset(ref)))
        )
      # class Nollaversio

    # Tarjotaan normalisointimetodi varsinaisen luokan metodina.
    # Huomaa, että metaluokan metodi ei näy luokan olioille.
    def versio(self, ref):
      # Poimitaan uloimman versiointikäytännön (irtoversio) mukainen
      # versionumero ja etäisyys siihen (= 0).
      versio, indeksi, etaisyys = self.versio_indeksi_etaisyys(ref)
      assert not etaisyys
      versio += indeksi
      versio = '+'.join((re.sub(
        # PEP 440: +haara.X -pääte voi sisältää
        # vain ASCII-kirjaimia, numeroita ja pisteitä.
        '[^a-zA-Z0-9.]', '', s
      ) for s in versio.split('+', 1)))
      try:
        return str(pkg_resources.packaging.version.Version(versio))
      except pkg_resources.packaging.version.InvalidVersion:
        return versio
      # def versio
    attrs['_versio'] = versio

    return super().__new__(mcs, name, tuple(bases), attrs)
    # def __new__

  # class VersiointiMeta

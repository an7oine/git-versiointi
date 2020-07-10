# -*- coding: utf-8 -*-

import itertools

import pkg_resources

from .oletus import KEHITYSVERSIO


class Kaytanto(type):
  '''
  Yksittäisen versiointikäytännön tyyppi.
  '''
  def __new__(mcs, name, bases, attrs, *, i=None, tyyppi=None, kaytanto=None):
    if i is not None:
      name = f'{name}_{i}'
    return super().__new__(mcs, name, bases, {
      **attrs,
      f'_{name}__tyyppi': tyyppi,
      f'_{name}__kaytanto': staticmethod(kaytanto),
      f'_{name}__valimuisti': {},
    })
    # def __new__

  @property
  def _tyyppi(cls):
    return getattr(cls, f'_{cls.__name__}__tyyppi')

  @property
  def _kaytanto(cls):
    return getattr(cls, f'_{cls.__name__}__kaytanto')

  @property
  def _valimuisti(cls):
    return getattr(cls, f'_{cls.__name__}__valimuisti')

  # class Kaytanto


class VersiointiMeta(Kaytanto):
  '''
  Versiointikäytäntöjen järjestelmän tyyppi.
  '''
  def __new__(mcs, name, bases, attrs, *, kaytanto):
    # pylint: disable=no-member, unused-variable, protected-access

    # Muodostetaan määritetyn käytännön mukaiset muotoilufunktioit.
    # Poimitaan ensimmäinen ja viimeinen käytäntö erikseen.
    def muotoilija(aihio):
      # pylint: disable=eval-used
      return lambda **kwargs: eval(f'f"{aihio}"', kwargs)
    (_, leimakaytanto), *kaytannot, (_, irtokaytanto) = (
      (avain, muotoilija(arvo))
      for avain, arvo in kaytanto.items()
    )

    # Muodostetaan luokkahierarkia käytäntöjen mukaan.
    class Irtoversio(metaclass=Kaytanto, kaytanto=irtokaytanto):
      def versio_ja_etaisyys(self, ref, leima, etaisyys):
        versio, etaisyys = super().versio_ja_etaisyys(ref, leima, etaisyys)
        if etaisyys:
          return __class__._kaytanto(
            ref=ref, versio=versio, etaisyys=etaisyys
          ), 0
        else:
          return versio, etaisyys
      # class Irtoversio
    bases += (Irtoversio, )

    for i, (tyyppi, kaytanto) in enumerate(reversed(kaytannot)):
      class Haaraversio(
        metaclass=Kaytanto, i=i, tyyppi=tyyppi, kaytanto=kaytanto
      ):
        def versio_ja_etaisyys(self, ref, leima, etaisyys):
          versio, etaisyys = super().versio_ja_etaisyys(ref, leima, etaisyys)
          if not etaisyys:
            return versio, etaisyys
          tyyppi, kaytanto = __class__._tyyppi, __class__._kaytanto
          valimuisti = __class__._valimuisti
          def etsi_haara(ref):
            haara = self.tietovarasto.haara(ref, tyyppi)
            if haara is not None:
              return ref, haara, 0
            isannat, j = self.tietovarasto.muutos(ref).parents, 1
            isanta = None
            while True:
              for isanta in isannat:
                haara = self.tietovarasto.haara(isanta, tyyppi)
                if haara is not None:
                  return isanta, haara, etaisyys
              isannat = sum((isanta.parents for isanta in isannat), ())
              j += 1
              if j >= etaisyys:
                break
            return None, None, None
          muutos, haara, j = etsi_haara(ref)
          if haara is not None:
            return kaytanto(
              ref=muutos, haara=haara.split('/')[-1],
              versio=versio, etaisyys=etaisyys-j,
            ), j
          #for j, muutos in enumerate(itertools.islice(
          #  self.tietovarasto.muutokset(ref), etaisyys
          #)):
          #  haara = self.tietovarasto.haara(muutos, tyyppi)
          #  if haara is not None:
          #    return kaytanto(
          #      ref=muutos, haara=haara.split('/')[-1],
          #      versio=versio, etaisyys=etaisyys-j,
          #    ), j
          #  # for j, muutos in enumerate(itertools.islice
          return versio, etaisyys
          # def versio_ja_etaisyys
        # class Haaraversio
      bases += (Haaraversio, )

    class LeimattuVersio(metaclass=Kaytanto, kaytanto=leimakaytanto):
      def versio_ja_etaisyys(self, ref, leima, etaisyys):
        # pylint: disable=unused-argument
        class SummautuvaLeima(str):
          def __add__(self, etaisyys):
            kehitysversio = KEHITYSVERSIO.match(self)
            if kehitysversio:
              if kehitysversio.group(2):
                etaisyys += int(kehitysversio.group(2))
              return type(self)(f'{kehitysversio.group(1)}{etaisyys}')
            return None
            # def __add__
          # class SummautuvaLeima
        return SummautuvaLeima(__class__._kaytanto(leima=leima)), etaisyys
      # class LeimattuVersio
    bases += (LeimattuVersio, )

    # Tarjotaan normalisointimetodi varsinaisen luokan metodina.
    # Huomaa, että metaluokan metodi ei näy luokan olioille.
    def versio(self, ref, leima, etaisyys):
      versio, etaisyys = self.versio_ja_etaisyys(ref, leima, etaisyys)
      assert not etaisyys, f'{versio} + {etaisyys}'
      versio = '+'.join((s.replace('+', '.') for s in versio.split('+', 1)))
      try:
        return str(pkg_resources.packaging.version.Version(versio))
      except pkg_resources.packaging.version.InvalidVersion:
        return versio
      # def versio
    attrs['_versio'] = versio

    return super().__new__(mcs, name, bases, attrs)
    # def __new__

  # class VersiointiMeta

# -*- coding: utf-8 -*-

import warnings

import pkg_resources

from .repo import Tietovarasto


class Versiointi:
  '''
  Versiointikäytäntö:
    versio (callable / str): version numerointi, oletus `"{leima}"`
    aliversio (callable / str): aliversion numerointi,
      oletus `"{leima}.{etaisyys}"`
  '''
  def __init__(
    self, polku, versio=None, aliversio=None, **kwargs
  ):
    if kwargs:
      warnings.warn(
        f'Tuntemattomat versiointiparametrit: {kwargs!r}', stacklevel=3
      )

    super().__init__()
    self.tietovarasto = Tietovarasto(polku)
    def muotoilija(aihio):
      def muotoilija(**kwargs):
        # pylint: disable=exec-used
        exec(f'tulos = f"{aihio}"', kwargs)
        return kwargs['tulos']
      return muotoilija

    if callable(versio):
      self.versio = versio
    else:
      assert versio is None or isinstance(versio, str)
      self.versio = (
        '{leima}'.format if not versio
        else muotoilija(versio)
      )

    if callable(aliversio):
      self.aliversio = aliversio
    else:
      assert aliversio is None or isinstance(aliversio, str)
      self.aliversio = (
        '{leima}.{etaisyys}'.format if not aliversio
        else muotoilija(aliversio)
      )
    # def __init__


  # SISÄISET METODIT

  @staticmethod
  def _normalisoi(versio):
    try:
      return str(pkg_resources.packaging.version.Version(versio))
    except pkg_resources.packaging.version.InvalidVersion:
      return versio
    # def _normalisoi

  def _muotoile(self, leima, etaisyys):
    '''
    Määritä versionumero käytännön mukaisesti
    versiolle, kehitysversiolle ja aliversiolle.

    Args:
      leima (git.Tag): lähin git-leima (tag)
      etaisyys (int): muutosten lukumäärä leiman jälkeen
    '''
    if leima is not None:
      kehitysversio = self.tietovarasto.KEHITYSVERSIO.match(str(leima))
      if kehitysversio:
        if kehitysversio.group(2):
          etaisyys += int(kehitysversio.group(2))
        return self._normalisoi(f'{kehitysversio.group(1)}{etaisyys}')

    return self._normalisoi((self.aliversio if etaisyys else self.versio)(
      leima=leima or 'v0.0',
      etaisyys=etaisyys,
    ))
    # def _muotoile


  # ULKOISET METODIT

  def versionumero(self, ref=None):
    '''
    Muodosta versionumero git-tietovaraston leimojen mukaan.
    Args:
      ref (str): git-viittaus (oletus HEAD)
    Returns:
      versionumero (str): esim. '1.0.2'
    '''
    # Jos viittaus osoittaa suoraan johonkin
    # julkaisuun tai kehitysversioon, palauta se.
    leima = (
      self.tietovarasto.leima(ref, kehitysversio=False)
      or self.tietovarasto.leima(ref, kehitysversio=True)
    )
    if leima:
      return self._muotoile(leima=leima, etaisyys=0)

    ref = self.tietovarasto.muutos(ref)

    # Etsi lähin leima ja palauta määritetyn käytännön mukainen aliversio:
    # oletuksena `leima.n`, missä `n` on etäisyys.
    etaisyys = 1
    # pylint: disable=redefined-argument-from-local
    for ref in ref.iter_parents():
      leima = self.tietovarasto.leima(ref, kehitysversio=True)
      if leima:
        return self._muotoile(leima=leima, etaisyys=etaisyys)
      etaisyys += 1

    # Jos yhtään aiempaa versiomerkintää ei löytynyt,
    # muodosta versionumero git-historian pituuden mukaan.
    return self._muotoile(leima=None, etaisyys=etaisyys)
    # def versionumero

  def historia(self, ref=None):
    '''
    Muodosta versiohistoria git-tietovaraston sisällön mukaan.

    Args:
      ref (str): git-viittaus (oletus HEAD)

    Yields:
      muutos (tuple): versio ja viesti, uusin ensin, esim.
        ``('1.0.2', 'Lisätty uusi toiminnallisuus Y')``,
        ``('1.0.1', 'Lisätty uusi toiminnallisuus X')``, ...
    '''
    # pylint: disable=redefined-argument-from-local
    for ref, leima, etaisyys in self.tietovarasto.muutosloki(ref):
      if getattr(leima, 'object', None) == ref and not etaisyys:
        yield {
          'tyyppi': 'julkaisu',
          'tunnus': ref.hexsha,
          'versio': self._muotoile(leima=leima, etaisyys=0),
          'kuvaus': getattr(leima.tag, 'message', '').rstrip('\n'),
        }
      else:
        yield {
          'tyyppi': 'muutos',
          'tunnus': ref.hexsha,
          'versio': self._muotoile(leima=leima, etaisyys=etaisyys),
          'kuvaus': ref.message.rstrip('\n'),
        }
      # for muutos in _git_historia
    # def historia

  def revisio(self, haettu_versio=None, ref=None):
    '''
    Palauta viimeisin git-revisio, jonka kohdalla
    versionumero vastaa annettua.

    Args:
      haettu_versio (str / None): esim. '1.0.2' (oletus nykyinen)
      ref: git-viittausmerkintä, josta haku aloitetaan (oletus HEAD)

    Returns:
      ref (str): git-viittaus
    '''
    versio = self._normalisoi(haettu_versio) if haettu_versio else None
    for pref, leima, etaisyys in self.tietovarasto.muutosloki(ref):
      if versio is None or self._muotoile(leima, etaisyys=etaisyys) == versio:
        return pref
      # for ref, leima, etaisyys in _git_muutosloki
    return None
    # def revisio

  # class Versiointi

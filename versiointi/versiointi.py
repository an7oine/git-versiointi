# -*- coding: utf-8 -*-

import itertools
import re
import warnings

import pkg_resources

from .repo import Tietovarasto


class Versiointi:
  '''
  Versiointikäytäntö:
    versio (callable / str): version numerointi, oletus `"{leima}"`
    aliversio (callable / str): aliversion numerointi,
      oletus `"{leima}.{etaisyys}"`
    oksaversio (callable / str): oksaversion numerointi,
      oletus `"{master}+{haara}.{oksa}"`
  '''
  def __init__(
    self, polku, versio=None, aliversio=None, oksaversio=None, **kwargs
  ):
    if kwargs:
      warnings.warn(
        f'Tuntemattomat versiointiparametrit: {kwargs!r}', stacklevel=3
      )

    super().__init__()

    try:
      self.tietovarasto = Tietovarasto(polku)
    except:
      raise ValueError(f'Git-tietovarastoa ei voitu avata polussa {polku!r}')

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

    if callable(oksaversio):
      self.oksaversio = oksaversio
    else:
      # Huom. asetetaan `None`,
      # mikäli oksaversiona on annettu tyhjä merkkijono.
      # Tällöin oksat versioidaan kuten master-haara.
      assert oksaversio is None or isinstance(oksaversio, str)
      self.oksaversio = (
        '{master}+{haara}.{oksa}'.format if oksaversio is None
        else None if not oksaversio
        else muotoilija(oksaversio)
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

  def _muotoile(self, leima=None, etaisyys=0, oksa=None):
    '''
    Määritä versionumero käytännön mukaisesti
    versiolle, kehitysversiolle ja aliversiolle.

    Args:
      leima (git.Tag): lähin git-leima (tag)
      etaisyys (int): muutosten lukumäärä leiman jälkeen
    '''
    if oksa is not None and self.oksaversio is not None:
      return self._normalisoi(self.oksaversio(**oksa))

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

  def _oksan_tiedot(self, ref=None):
    master, oksa = self.tietovarasto.oksa(ref)
    if not oksa:
      return itertools.repeat(None)
    param = {'master': self.versionumero(master)}
    for haara in self.tietovarasto.vierashaarat:
      if self.tietovarasto.muutos(ref) in self.tietovarasto.muutokset(haara):
        param['haara'] = re.sub(
          # PEP 404: +haara.X -pääte voi sisältää
          # vain ASCII-kirjaimia, numeroita ja pisteitä.
          '[^a-zA-Z0-9.]', '', haara.remote_head
        )
        break
    else:
      return itertools.repeat(None)
    return itertools.chain(
      ({'oksa': oksa, **param} for oksa in range(oksa, 0, -1)),
      itertools.repeat(None)
    )
    # def _oksan_tiedot


  # ULKOISET METODIT

  def versionumero(self, ref=None):
    '''
    Muodosta versionumero git-tietovaraston leimojen mukaan.
    Args:
      ref (str): git-viittaus (oletus HEAD)
    Returns:
      versionumero (str): esim. '1.0.2'
    '''
    # Tarkista ensin, että muutos on olemassa.
    try: self.tietovarasto.muutos(ref)
    except ValueError:
      # Muodosta väliaikainen versionumero tyyppiä 0.0.
      return self._muotoile(leima=None, etaisyys=0)

    # Jos viittaus osoittaa suoraan johonkin
    # julkaisuun tai kehitysversioon, palauta se.
    leima = (
      self.tietovarasto.leima(ref, kehitysversio=False)
      or self.tietovarasto.leima(ref, kehitysversio=True)
    )
    if leima:
      return self._muotoile(leima=leima, etaisyys=0, oksa=None)

    oksa = next(self._oksan_tiedot(ref))

    ref = self.tietovarasto.muutos(ref)

    # Etsi lähin leima ja palauta määritetyn käytännön mukainen aliversio:
    # oletuksena `leima.n`, missä `n` on etäisyys.
    etaisyys = 1
    # pylint: disable=redefined-argument-from-local
    for ref in ref.iter_parents():
      leima = self.tietovarasto.leima(ref, kehitysversio=True)
      if leima:
        return self._muotoile(
          leima=leima,
          etaisyys=etaisyys,
          oksa=oksa if oksa is not None and oksa['oksa'] <= etaisyys else None,
        )
      etaisyys += 1

    # Jos yhtään aiempaa versiomerkintää ei löytynyt,
    # muodosta versionumero git-historian pituuden mukaan.
    return self._muotoile(leima=None, etaisyys=etaisyys, oksa=oksa)
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
    # pylint: disable=stop-iteration-return
    # Tarkista ensin, että muutos on olemassa.
    try: self.tietovarasto.muutos(ref)
    except ValueError: return

    oksan_tiedot = self._oksan_tiedot(ref)
    for ref, leima, etaisyys in self.tietovarasto.muutosloki(ref):
      if getattr(leima, 'object', None) == ref and not etaisyys:
        yield {
          'tyyppi': 'julkaisu',
          'tunnus': ref.hexsha,
          'versio': self._muotoile(
            leima=leima, etaisyys=0, oksa=next(oksan_tiedot),
          ),
          'kuvaus': getattr(leima.tag, 'message', '').rstrip('\n'),
        }
      else:
        yield {
          'tyyppi': 'muutos',
          'tunnus': ref.hexsha,
          'versio': self._muotoile(
            leima=leima, etaisyys=etaisyys, oksa=next(oksan_tiedot),
          ),
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

# -*- coding: utf-8 -*-

import itertools
import warnings

from pkg_resources import parse_version

from .kaytanto import VersiointiMeta
from .oletus import VERSIOKAYTANTO
from .repo import Tietovarasto


class Versiointi:
  '''Versiointikäytäntö.

  Args:
    polku (str): git-tietovaraston polku
    kaytanto (dict): versiointikäytäntö
    historian_pituus (int): tallennettavan muutoshistorian
      enimmäispituus, oletus rajoittamaton
  '''

  def __new__(cls, *_, kaytanto=None, **__):
    return super().__new__(
      VersiointiMeta(
        cls.__name__, (cls, ), {},
        kaytanto=kaytanto or VERSIOKAYTANTO
      ),
    )
    # def __new__

  def __init__(self, polku, kaytanto=None, historian_pituus=None, **kwargs):
    # pylint: disable=unused-argument
    if kwargs:
      warnings.warn(
        f'Tuntemattomat versiointiparametrit: {kwargs!r}', stacklevel=3
      )

    super().__init__()
    try:
      self.tietovarasto = Tietovarasto(polku)
    except Exception as exc:
      raise ValueError(
        f'Git-tietovarastoa ei voitu avata polussa {polku!r}: {exc}'
      )

    self.historian_pituus = historian_pituus
    # def __init__

  # Korvataan versiointikäytännön mukaisella toteutuksella.
  def _versio(self, *_): raise NotImplementedError

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
    except ValueError: return None

    etaisyys = 0
    leima = self.tietovarasto.leima(ref, kehitysversio=False)
    if leima is None:
      for etaisyys, muutos in enumerate(self.tietovarasto.muutokset(ref)):
        leima = self.tietovarasto.leima(muutos, kehitysversio=True)
        if leima:
          break
    return self._versio(ref, leima, etaisyys)
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

    for ref, leima, etaisyys in itertools.islice(
      self.tietovarasto.muutosloki(ref), self.historian_pituus
    ):
      if getattr(leima, 'object', None) == ref and not etaisyys:
        yield {
          'tyyppi': 'julkaisu',
          'tunnus': ref.hexsha,
          'versio': self._versio(ref, leima, etaisyys),
          'kuvaus': getattr(leima.tag, 'message', '').rstrip('\n'),
        }
      else:
        yield {
          'tyyppi': 'muutos',
          'tunnus': ref.hexsha,
          'versio': self._versio(ref, leima, etaisyys),
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
      ref: git-revisio, josta haku aloitetaan (oletus HEAD)

    Returns:
      ref (str): git-viittaus
    '''
    versio = str(parse_version(haettu_versio)) if haettu_versio else None
    for muutos, leima, etaisyys in self.tietovarasto.muutosloki(ref):
      if versio is None or self._versio(
        muutos, leima, etaisyys
      ) == versio:
        return muutos
      # for muutos, leima, etaisyys in _git_muutosloki
    return None
    # def revisio

  # class Versiointi

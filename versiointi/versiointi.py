# -*- coding: utf-8 -*-

import itertools
import warnings

from pkg_resources import parse_version

from .kaytanto import VersiointiMeta
from .repo import Tietovarasto


class Versiointi:
  '''Versiointikäytäntö.

  Args:
    polku (str): git-tietovaraston polku
    kaytanto (dict): versiointikäytäntö
    historian_pituus (int): tallennettavan muutoshistorian
      enimmäispituus, oletus rajoittamaton
  '''

  def __new__(cls, *_, kaytanto, **__):
    # Luodaan metaluokka dynaamisesti `kaytanto`-parametrin mukaan.
    # Huomaa, että `type.__call__` kutsuu `__init__`-metodia annetuilla
    # parametreillä (*args ja **kwargs), joten ne sivuutetaan tässä.
    return super().__new__(
      VersiointiMeta(
        cls.__name__, (cls, ), {},
        kaytanto=kaytanto,
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
      ) from exc

    self.historian_pituus = historian_pituus
    # def __init__

  def _versio(self, ref):
    '''
    Palauta annettua muutosta vastaava versionumero.

    Metaluokka korvaa tämän versiointikäytännön mukaisella
    toteutuksella.
    '''
    raise NotImplementedError

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
    else: return self._versio(ref)
    # def versionumero

  def historia(self, ref=None):
    '''
    Muodosta versiohistoria git-tietovaraston sisällön mukaan.

    Args:
      ref (str): git-viittaus (oletus HEAD)

    Yields:
      muutos: {
        'revisio': 'deadbeef',
        'versio': '1.2.3',
        'kuvaus': 'Lisätty uusi toiminnallisuus',
      }
    '''
    # pylint: disable=redefined-argument-from-local
    # pylint: disable=stop-iteration-return

    # Tarkista ensin, että muutos on olemassa.
    try: self.tietovarasto.muutos(ref)
    except ValueError: return

    for ref in itertools.islice(
      self.tietovarasto.muutokset(ref), self.historian_pituus
    ):
      yield {
        'revisio': ref.hexsha,
        'versio': self._versio(ref),
        'kuvaus': ref.message.rstrip('\n'),
      }
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
    for muutos in self.tietovarasto.muutokset(ref):
      if versio is None or self._versio(muutos) == versio:
        return muutos
    return None
    # def revisio

  # class Versiointi

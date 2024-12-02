# -*- coding: utf-8 -*-
# pylint: disable=protected-access

import itertools
import os
import re


VERSIOINTI = re.compile(
  r'^# versiointi: ((\w+)|[*])$'
)


def tiedostoversiot(versiointi, tiedosto):
  '''Hae tiedostossa määritetyn käytännön mukaiset aiemmat versiot.

  Args:
    versiointi (Versiointi)
    tiedosto (str): suhteellinen tiedostonimi
      alkaen git-projektin juuresta

  Yields:
    (versionumero, tiedostosisältö)
  '''
  # Tutki, sisältyykö versiointimääritys ensimmäisiin 10 riviin.
  with open(os.path.join(
    versiointi.tietovarasto.working_tree_dir,
    tiedosto
  ), 'r') as tiedostosisalto:
    for rivi in itertools.islice(tiedostosisalto, 10):
      tiedoston_versiointi = VERSIOINTI.match(rivi)
      if tiedoston_versiointi:
        alkaen = tiedoston_versiointi[2]
        break
    else:
      # Ellei, poistutaan nopeasti.
      return
    # with tiedostosisalto

  # Käy läpi kyseistä tiedostoa koskevat muutokset,
  # tuota versionumero ja tiedstosisältö kunkin muutoksen kohdalla.
  for ref in versiointi.tietovarasto.git.rev_list(
    f'{alkaen}..HEAD' if alkaen else 'HEAD', '--', tiedosto
  ).splitlines():
    yield versiointi.versionumero(ref), versiointi.tietovarasto.git.show(
      ref + ':' + tiedosto, stdout_as_string=False
    )
    # for ref in versiointi.tietovarasto.git.rev_list
  # def tiedostoversiot


class Versioitu:
  git_versiointi = None

  def _kopioi_moduulin_versiot(self, lahde, kohde):
    for versionumero, tiedostosisalto in tiedostoversiot(
      self.git_versiointi, lahde
    ):
      # Muodosta tulostiedoston nimi.
      outfile = f'-{versionumero}'.join(os.path.splitext(kohde))

      # Kirjoita sisältö tulostiedostoon ja tuota sen nimi.
      with open(outfile, 'wb') as tiedosto:
        tiedosto.write(tiedostosisalto)
        yield outfile
        # with open as tiedosto
      # for versionumero, tiedostosisalto in tiedostoversiot
    # def _kopioi_moduulin_versiot

  # class Versioitu


class build_py(Versioitu):
  # pylint: disable=function-redefined, invalid-name, no-member

  def build_module(self, module, module_file, package):
    # Asenna tiedosto normaalisti.
    oletustulos = super().build_module(module, module_file, package)
    if self.git_versiointi is None:
      return oletustulos

    # Ks. `distutils.command.build_py.build_py.build_module`.
    if isinstance(package, str):
      package = package.split('.')

    # Tallenna tiedoston versio kunkin muutoksen kohdalla;
    # lisää tiedostonimeen vastaava versionumero.
    for versioitu_tiedosto in self._kopioi_moduulin_versiot(
      module_file,
      self.get_module_outfile(self.build_lib, package, module),
    ):
      # Setuptools < 75.6.0.
      try:
        bpuf = self._build_py__updated_files
      except AttributeError:
        pass
      else:
        bpuf.append(versioitu_tiedosto)
        # else
      # for versioitu_tiedosto in self._kopioi_moduulin_versiot

    # Palautetaan kuten oletus.
    return oletustulos
    # def build_module
  # class build_py


class sdist(Versioitu):
  # pylint: disable=no-member

  def copy_file(
    self,
    infile,
    outfile,
    preserve_mode=1,
    preserve_times=1,
    link=None,
    level=1
  ):
    ''' Kopioi alkuperäisen lisäksi mahdolliset versioidut moduulit. '''
    tulos = super().copy_file(
      infile,
      outfile,
      preserve_mode=preserve_mode,
      preserve_times=preserve_times,
      link=link,
      level=level
    )
    list(self._kopioi_moduulin_versiot(
      infile,
      outfile
    ))
    return tulos
    # def copy_file

  # class sdist

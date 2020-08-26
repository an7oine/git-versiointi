# -*- coding: utf-8 -*-
# pylint: disable=protected-access

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
  # Tutki, sisältääkö tiedostosisältö versiointimäärityksen.
  with open(os.path.join(
    versiointi.tietovarasto.working_tree_dir,
    tiedosto
  ), 'r') as tiedostosisalto:
    for rivi in tiedostosisalto:
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


class build_py:
  # pylint: disable=invalid-name, no-member
  git_versiointi = None
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
    for versionumero, tiedostosisalto in tiedostoversiot(
      self.git_versiointi, module_file
    ):
      # Muodosta tulostiedoston nimi.
      outfile = self.get_module_outfile(self.build_lib, package, module)
      outfile = f'-{versionumero}'.join(os.path.splitext(outfile))

      # Kirjoita sisältö tulostiedostoon, tee muistiinpano.
      with open(outfile, 'wb') as tiedosto:
        tiedosto.write(tiedostosisalto)
      self._build_py__updated_files.append(outfile)

      # for versionumero, tiedostosisalto in tiedostoversiot

    # Palautetaan kuten oletus.
    return oletustulos
    # def build_module
  # class build_py

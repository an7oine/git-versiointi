# -*- coding: utf-8 -*-
# pylint: disable=protected-access

import os
import re


VERSIOINTI = re.compile(
  r'^# versiointi: ((\w+)|[*])$'
)

def tiedostokohtainen_versiointi(komento, versiointi):
  oletus = komento.build_module

  def build_module(self, module, module_file, package):
    # Asenna tiedosto normaalisti.
    oletustulos = oletus(self, module, module_file, package)

    # Tutki, sisältääkö tiedostosisältö versiointimäärityksen.
    with open(module_file, 'r') as tiedosto:
      for rivi in tiedosto:
        tiedoston_versiointi = VERSIOINTI.match(rivi)
        if tiedoston_versiointi:
          alkaen = tiedoston_versiointi[2]
          break
      else:
        # Ellei, poistutaan nopeasti.
        return oletustulos
      # with tiedosto

    # Ks. `distutils.command.build_py.build_py.build_module`.
    if isinstance(package, str):
      package = package.split('.')

    # Käy läpi kyseistä tiedostoa koskevat muutokset,
    # tallenna tiedoston kunkin muutoksen kohdalla
    # lisäten tiedostonimeen muutosta vastaava versionumero.
    for ref in versiointi.tietovarasto.git.rev_list(
      f'{alkaen}..HEAD' if alkaen else 'HEAD', '--', module_file
    ).splitlines():
      versionumero = versiointi.versionumero(ref)
      outfile = self.get_module_outfile(self.build_lib, package, module)
      outfile = f'-{versionumero}'.join(os.path.splitext(outfile))
      with open(outfile, 'wb') as tiedosto:
        tiedosto.write(versiointi.tietovarasto.git.show(
          ref + ':' + module_file, stdout_as_string=False
        ))
        # with open as tiedosto
      self._build_py__updated_files.append(outfile)
      # for ref in versiointi.tietovarasto.git.rev_list

    # Palautetaan kuten oletus.
    return oletustulos
    # def build_module

  komento.build_module = build_module
  # def tiedostokohtainen_versiointi

import subprocess
import zipfile

from ._tietovarasto import Tietovarasto


class Testit(Tietovarasto):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    with open(
      cls.hakemisto / 'pyproject.toml',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('[build-system]\n')
      kahva.write('requires = ["git-versiointi", "setuptools"]\n')
      kahva.write('build-backend = "setuptools.build_meta"\n')
      kahva.write('[project]\n')
      kahva.write('name = "testi"\n')
      kahva.write('dynamic = ["version"]\n')
    (cls.hakemisto / 'testi').mkdir()
    (cls.hakemisto / 'testi' / '__init__.py').touch()

    # Alkuperäinen sisältö.
    with open(
      cls.hakemisto / 'testi' / 'testi.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write('# versiointi: *\n')
      kahva.write('42')
    with open(
      cls.hakemisto / 'testi' / 'testi2.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write('42')
    with open(
      cls.hakemisto / 'testi' / 'testi3.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write('42')
    cls.repo.index.add([
      'pyproject.toml',
      'testi/__init__.py',
      'testi/testi.py',
      'testi/testi2.py',
      'testi/testi3.py',
    ])
    nolla = cls.repo.index.commit("Alustava toteutus")
    cls.repo.create_tag('v0.1')

    # Ensimmäinen muutos.
    with open(
      cls.hakemisto / 'testi' / 'testi.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write('# versiointi: *\n')
      kahva.write('43')
    with open(
      cls.hakemisto / 'testi' / 'testi2.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write(f'# versiointi: {nolla}\n')
      kahva.write('43')
    with open(
      cls.hakemisto / 'testi' / 'testi3.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write('43')
    cls.repo.index.add([
      'testi/testi.py',
      'testi/testi2.py',
      'testi/testi3.py',
    ])
    eka = cls.repo.index.commit("Ensimmäinen muutos")

    # Toinen muutos.
    with open(
      cls.hakemisto / 'testi' / 'testi.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write('# versiointi: *\n')
      kahva.write('44')
    with open(
      cls.hakemisto / 'testi' / 'testi2.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write(f'# versiointi: {nolla}\n')
      kahva.write('44')
    with open(
      cls.hakemisto / 'testi' / 'testi3.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write(f'# versiointi: {eka}\n')
      kahva.write('44')
    with open(
      cls.hakemisto / 'testi' / 'testi4.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('#!/usr/bin/env python\n')
      kahva.write('44')
    cls.repo.index.add([
      'testi/testi.py',
      'testi/testi2.py',
      'testi/testi3.py',
      'testi/testi4.py',
    ])
    cls.repo.index.commit("Toinen muutos")
    # def setUpClass

  def _varmista_versioitu_sisalto(self):
    with zipfile.ZipFile(
      self.hakemisto
      / 'dist'
      / 'testi-0.1.2-py3-none-any.whl'
    ) as whl:
      # Tiedosto `testi.py`: versiot 0.1, 0.1.1 ja 0.1.2.
      self.assertIn(
        '44',
        whl.read('testi/testi.py').decode().splitlines()
      )
      self.assertIn(
        '44',
        whl.read('testi/testi-0.1.2.py').decode().splitlines()
      )
      self.assertIn(
        '43',
        whl.read('testi/testi-0.1.1.py').decode().splitlines()
      )
      self.assertIn(
        '42',
        whl.read('testi/testi-0.1.py').decode().splitlines()
      )

      # Tiedosto `testi2.py`: versiot 0.1.1 ja 0.1.2.
      self.assertIn(
        '44',
        whl.read('testi/testi2.py').decode().splitlines()
      )
      self.assertIn(
        '44',
        whl.read('testi/testi2-0.1.2.py').decode().splitlines()
      )
      self.assertIn(
        '43',
        whl.read('testi/testi2-0.1.1.py').decode().splitlines()
      )
      with self.assertRaises(KeyError):
        whl.read('testi/testi2-0.1.py')

      # Tiedosto `testi3.py`: vain versio 0.1.2.
      self.assertIn(
        '44',
        whl.read('testi/testi3.py').decode().splitlines()
      )
      self.assertIn(
        '44',
        whl.read('testi/testi3-0.1.2.py').decode().splitlines()
      )
      with self.assertRaises(KeyError):
        whl.read('testi/testi3-0.1.1.py')

      # Tiedosto `testi4.py`: ei versiointia.
      self.assertIn(
        '44',
        whl.read('testi/testi4.py').decode().splitlines()
      )
      with self.assertRaises(KeyError):
        whl.read('testi/testi4-0.1.2.py')
      # with zipfile.ZipFile
    # def _varmista_versioitu_sisalto

  def testaa_tiedostot_setup_py(self):
    '''
    Tallennetaanko tiedostoversiot komennolla `python setup.py bdist_wheel`?
    '''
    with open(
      self.hakemisto / 'setup.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('from setuptools import setup\n')
      kahva.write(
        'setup(setup_requires=["git-versiointi", "setuptools"])\n'
      )
    subprocess.run(
      [
        'python',
        'setup.py',
        'bdist_wheel',
      ],
      capture_output=True,
      check=True,
      cwd=self.hakemisto,
    )
    self._varmista_versioitu_sisalto()
    # def testaa_tiedostot_setup_py

  def testaa_tiedostot_pep517(self):
    '''
    Tallennetaanko tiedostoversiot komennolla `python -m build`?
    '''
    subprocess.run(
      [
        'python',
        '-m',
        'build',
        '--no-isolation',
      ],
      capture_output=True,
      check=True,
      cwd=self.hakemisto,
    )
    self._varmista_versioitu_sisalto()
    # def testaa_tiedostot_pep517

  # class Testit

import subprocess

from metadata import build_metadata, parse_metadata

from ._tietovarasto import Tietovarasto


class Testit(Tietovarasto):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    with open(
      cls.hakemisto / 'setup.py',
      'w',
      encoding='utf-8',
    ) as kahva:
      kahva.write('from setuptools import setup\n')
      kahva.write(
        'setup(name="testi", setup_requires=['
        '"git-versiointi>=1.7b1", "setuptools"])\n'
      )
    cls.repo.index.add(['setup.py'])
    cls.repo.index.commit("Alustava toteutus")
    cls.repo.create_tag('v0.1')

    cls.repo.index.commit("Muutos")
    cls.repo.create_tag('v0.2')
    # def setUpClass

  def testaa_metadata_pep517(self):
    self.assertEqual(
      parse_metadata(
        build_metadata(self.hakemisto, isolation=False),
        'version'
      ),
      ['0.2']
    )
    # def testaa_metadata_pep517

  def testaa_koonti_pep517(self):
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
    self.assertTrue(
      (
        self.hakemisto
        / 'dist'
        / 'testi-0.2.tar.gz'
      ).exists()
    )
    self.assertTrue(
      (
        self.hakemisto
        / 'dist'
        / 'testi-0.2-py3-none-any.whl'
      ).exists()
    )
    # def testaa_koonti_pep517

  def testaa_metadata_setuptools(self):
    ajo = subprocess.run(
      [
        'python',
        'setup.py',
        '--version'
      ],
      capture_output=True,
      check=True,
      cwd=self.hakemisto,
    )
    self.assertEqual(
      ajo.stdout.decode().split('\n')[0],
      '0.2'
    )


  def testaa_metadata_setuptools_2(self):
    with self._ohita_setuptools_bugi():
      ajo = subprocess.run(
        [
          'python',
          self.hakemisto / 'setup.py',
          '--version'
        ],
        check=True,
        capture_output=True,
      )
      self.assertEqual(
        ajo.stdout.decode().split('\n')[0],
        '0.2'
      )
    # def testaa_metadata_setuptools_2

  def testaa_sdist(self):
    subprocess.run(
      [
        'python',
        'setup.py',
        'sdist',
      ],
      capture_output=True,
      check=True,
      cwd=self.hakemisto,
    )
    self.assertTrue(
      (
        self.hakemisto
        / 'dist'
        / 'testi-0.2.tar.gz'
      ).exists()
    )
    # def testaa_sdist

  def testaa_bdist_wheel(self):
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
    self.assertTrue(
      (
        self.hakemisto
        / 'dist'
        / 'testi-0.2-py3-none-any.whl'
      ).exists()
    )
    # def testaa_bdist_wheel

  def testaa_aiempi_versio_setuptools(self):
    ajo = subprocess.run(
      [
        'python',
        'setup.py',
        '--version',
        '--ref',
        'HEAD^',
      ],
      capture_output=True,
      check=True,
      cwd=self.hakemisto,
    )
    self.assertEqual(
      ajo.stdout.decode().split('\n')[0],
      '0.1'
    )
    # def testaa_aiempi_versio_setuptools

  # class Testit

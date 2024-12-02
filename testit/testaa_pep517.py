import subprocess

from metadata import build_metadata, parse_metadata

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
    cls.repo.index.add(['pyproject.toml'])
    cls.repo.index.commit("Alustava toteutus")
    cls.repo.create_tag('v0.1')
    # def setUpClass

  def testaa_metadata(self):
    self.assertEqual(
      parse_metadata(
        build_metadata(self.hakemisto, isolation=False),
        'version'
      ),
      ['0.1']
    )
    # def testaa_metadata

  def testaa_koonti(self):
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
        / 'testi-0.1.tar.gz'
      ).exists()
    )
    self.assertTrue(
      (
        self.hakemisto
        / 'dist'
        / 'testi-0.1-py3-none-any.whl'
      ).exists()
    )
    # def testaa_koonti

  # class Testit

from versiointi import _versiointi

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

    cls.repo.create_tag('nolla')
    nollahaara = cls.repo.create_head(
      'v-0.0',
      cls.repo.index.commit(
        'Nollavaihtoehto',
        head=False
      )
    )
    cls.repo.create_head(
      'ekahaara',
      cls.repo.index.commit(
        'Ensimmäinen vaihtoehto',
        [nollahaara.commit],
        head=False
      )
    )

    cls.repo.index.commit("Ensimmäinen muutos")
    cls.repo.create_tag('eka')

    cls.repo.index.commit("Toinen muutos")
    cls.repo.create_tag('toka')
    cls.repo.create_tag('v0.1')
    cls.repo.create_head(
      'tokahaara',
      cls.repo.index.commit(
        'Toinen vaihtoehto',
        head=False
      )
    )

    cls.repo.index.commit("Kolmas muutos")
    cls.repo.create_tag('kolmas')
    cls.repo.create_head(
      'kolmoshaara',
      cls.repo.index.commit(
        'Kolmas vaihtoehto',
        head=False
      )
    )

    cls.repo.index.commit("Neljäs muutos")
    cls.repo.create_tag('neljas')
    cls.repo.create_tag('v0.2c1')
    cls.repo.create_head(
      'neloshaara',
      cls.repo.index.commit(
        'Neljäs vaihtoehto',
        head=False
      )
    )

    cls.repo.index.commit("Viides muutos")
    cls.repo.create_tag('viides')
    viitoshaara = cls.repo.create_head(
      'viitoshaara',
      cls.repo.index.commit(
        'Viides vaihtoehto',
        head=False
      )
    )

    cls.repo.create_tag(
      'irto',
      cls.repo.index.commit(
        'Irtomuutos',
        [viitoshaara.commit],
        head=False
      )
    )
    # def setUpClass

  def setUp(self):
    super().setUp()
    self.versiointi = _versiointi(self.hakemisto)

  def testaa_nolla(self):
    self.assertEqual(
      self.versiointi.versionumero(ref='nolla'),
      '0.0.1'
    )
    # def testaa_nolla

  def testaa_eka(self):
    self.assertEqual(
      self.versiointi.versionumero(ref='ekahaara'),
      '0.0.3.dev0+1.ekahaara'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='eka'),
      '0.0.2'
    )
    # def testaa_eka

  def testaa_toka(self):
    self.assertEqual(
      self.versiointi.versionumero(ref='toka'),
      '0.1'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='tokahaara'),
      '0.1.1.dev0+1.tokahaara'
    )
    # def testaa_toka

  def testaa_kolmas(self):
    self.assertEqual(
      self.versiointi.versionumero(ref='kolmas'),
      '0.1.1'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='kolmoshaara'),
      '0.1.2.dev0+1.kolmoshaara'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='kolmoshaara^'),
      '0.1.1',
    )
    # def testaa_kolmas

  def testaa_neljas(self):
    self.assertEqual(
      self.versiointi.versionumero(ref='neljas'),
      '0.2rc1'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='neloshaara'),
      '0.2rc2.dev0+1.neloshaara'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='neloshaara^'),
      '0.2rc1'
    )
    # def testaa_neljas

  def testaa_viides(self):
    self.assertEqual(
      self.versiointi.versionumero(ref='viides'),
      '0.2rc2'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='viitoshaara'),
      '0.2rc3.dev0+1.viitoshaara'
    )
    self.assertEqual(
      self.versiointi.versionumero(ref='viitoshaara^'),
      '0.2rc2'
    )
    # def testaa_viides

  def testaa_irto(self):
    self.assertEqual(
      self.versiointi.versionumero(ref='irto'),
      f'0.2rc3.dev0+1.viitoshaara.1.dev1',
    )
    # def testaa_irto

  # class Testit

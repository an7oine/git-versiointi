from contextlib import contextmanager
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from git import Repo


class Tietovarasto(TestCase):

  @classmethod
  def setUpClass(cls):
    ''' Luo git-tietovarasto tilapäishakemistoon. '''
    super().setUpClass()
    cls.__hakemisto = TemporaryDirectory()
    cls.hakemisto = Path(cls.__hakemisto.__enter__())
    cls.repo = Repo.init(cls.hakemisto)
    # def setUpClass

  @classmethod
  def tearDownClass(cls):
    ''' Poista tilapäishakemisto. '''
    cls.__hakemisto.__exit__(None, None, None)
    super().tearDownClass()
    # def tearDownClass

  def setUp(self):
    ''' Poista ylimääräinen sisältö ennen kutakin testiä. '''
    super().setUp()
    self.repo.git.clean('-xdf')
    # def setUp

  @staticmethod
  @contextmanager
  def _ohita_setuptools_bugi():
    '''
    Vaihdetaan työhakemistoksi tyhjä tilapäishakemisto, mikäli
    nykyisessä työhakemistossa on `pyproject.toml`-tiedosto. Näin
    kierretään bugi setuptools-toteutuksessa, joka huomioi kyseisen
    tiedoston sisällön aina, kun mitä tahansa pakettia käsitellään.
    '''
    if ((alkuperainen_hakem := Path.cwd()) / 'pyproject.toml').exists():
      with TemporaryDirectory() as tilapainen_hakem:
        os.chdir(tilapainen_hakem)
        try:
          yield
        finally:
          os.chdir(alkuperainen_hakem)
    else:
      yield
      # else
    # def _ohita_setuptools_bugi

  # class Tietovarasto

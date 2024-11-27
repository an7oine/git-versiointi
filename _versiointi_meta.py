# Kierretään PEP 517 -rajoitus: backend-path < build-backend.
from setuptools.build_meta import *


def __getattr__(avain: str):
  '''
  Moduulimääre `versio`: muodosta, vie välimuistiin ja palauta
  `git-versioinnin` oma versionumero.
  '''
  if avain == 'versio':
    from versiointi import _versionumero
    global versio
    return (versio := _versionumero(__file__))

  raise AttributeError(avain)

# -*- coding: utf-8 -*-

from distutils.errors import DistutilsSetupError
import json
import os
from types import GeneratorType


def varmista_json(dist, attr, value):
  if not isinstance(value, GeneratorType):
    raise DistutilsSetupError(
      f'Vaaditaan `GeneratorType`, annettiin `{type(value)}`.'
    )


def kirjoita_json(cmd, basename, filename):
  argname = os.path.splitext(basename)[0]
  data = getattr(cmd.distribution, argname, None)
  if data is not None:
    cmd.write_or_delete_file(
      argname, filename, json.dumps(list(data), indent=2)
    )

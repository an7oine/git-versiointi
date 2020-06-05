# -*- coding: utf-8 -*-

import re


# Leimat, jotka tunnistetaan versiomerkinnöiksi.
VERSIO = re.compile(r'^v[0-9]', flags=re.IGNORECASE)

# Leimatut versiot, jotka tunnistetaan kehitysversioiksi.
KEHITYSVERSIO = re.compile(r'(.+[a-z])([0-9]*)$', flags=re.IGNORECASE)

# Oletusversiokäytäntö.
VERSIOKAYTANTO = {
  'refs/tags/': '''{leima or '0.0'}''',
  'refs/heads/master refs/remotes/origin/master': (
    '''{versio+etaisyys or f'{versio}.{etaisyys}'}'''
  ),
  'refs/heads/ refs/remotes/origin/': '{versio}+{haara}.{etaisyys}',
  '*': '''{versio}+{etaisyys}''',
}

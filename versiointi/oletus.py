# -*- coding: utf-8 -*-

# Oletusversiokäytäntö.
VERSIOKAYTANTO = {
  # pylint: disable=line-too-long

  # Irtoversio (nk. detached HEAD).
  '*': '''{pohja}+{etaisyys}''',

  # (Muun kuin master-) haaran versio:
  # indeksoitu kehitysversio tai haaran mukainen tunniste.
  'refs/heads/ refs/remotes/origin/': (
    '''{pohja}{int(indeksi)+etaisyys if indeksi else f'+{tunnus}.{etaisyys}'}'''
  ),

  # Master-haara tai versiohaara (v-X.Y):
  # indeksoitu kehitysversio tai etäisyyden mukainen pääte.
  ' '.join((
    'refs/heads/master',
    'refs/remotes/origin/master',
    'refs/heads/v-[0-9].*',
    'refs/remotes/origin/v-[0-9].*',
  )): (
    '''{pohja}{int(indeksi)+etaisyys if indeksi else f'.{etaisyys}'}'''
  ),

  # Leimattu kehitysversiosarja: tulkitaan viimeinen luku indeksinä.
  'refs/tags/v[0-9].*': '''{tunnus[1:]}{indeksoitu}''',

  # Leimattu (ei-kehitys-) versio: käytetään sellaisenaan.
  'refs/tags/v[0-9][0-9.]*?(?![a-z]+[0-9]*)': '''{tunnus[1:]}''',

  # Nollaversio (edeltää ensimmäistä leimaa).
  '0': '0.0',
}

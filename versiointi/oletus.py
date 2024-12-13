# -*- coding: utf-8 -*-

# Oletusversiokäytäntö.
VERSIOKAYTANTO = {
  # pylint: disable=line-too-long

  # Irtoversio (nk. detached HEAD): lisätään etäisyys.
  '*': '''{pohja}{int(indeksi)+1 if indeksi else ".1"}.dev+{etaisyys}''',

  # (Muun kuin master-) haaran versio:
  # indeksoitu kehitysversio tai haaran mukainen tunniste.
  'refs/heads/ refs/remotes/origin/': (
    '''{pohja}{int(indeksi)+1 if indeksi else ".1"}.dev+{etaisyys}.{tunnus}'''
  ),

  # Master-haara tai versiohaara (v-X.Y):
  # indeksoitu kehitysversio tai etäisyyden mukainen pääte.
  ' '.join((
    'refs/heads/(master|v-[0-9].*)',
    'refs/remotes/origin/(master|v-[0-9].*)',
  )): (
    '''{pohja}{int(indeksi)+etaisyys if indeksi else f'.{etaisyys}'}{indeksoitu}'''
  ),

  # Leimattu kehitysversiosarja: tulkitaan viimeinen luku indeksinä.
  'refs/tags/v[0-9].*': '''{tunnus[1:]}{indeksoitu}''',

  # Leimattu (ei-kehitys-) versio: poimitaan tunnus, poistetaan "v".
  'refs/tags/v[0-9][0-9.]*?(?![a-z]+[0-9]*)': '''{tunnus[1:]}''',

  # Nollaversio (edeltää ensimmäistä leimaa).
  '0': '0.0',
}

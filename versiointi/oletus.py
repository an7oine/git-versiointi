# -*- coding: utf-8 -*-

# Oletusversiokäytäntö.
VERSIOKAYTANTO = {
  # Irtoversio (nk. detached HEAD).
  '*': '''{pohja}+{etaisyys}''',

  # (Muun kuin master-) haaran versio:
  # indeksoitu kehitysversio tai haaran mukainen tunniste.
  'refs/heads/ refs/remotes/origin/': \
    '''{pohja}{int(indeksi)+etaisyys if indeksi else f'+{tunnus}.{etaisyys}'}''',

  # Master-haaran versio:
  # indeksoitu kehitysversio tai etäisyyden mukainen pääte.
  'refs/heads/master refs/remotes/origin/master': \
    '''{pohja}{int(indeksi)+etaisyys if indeksi else f'.{etaisyys}'}''',

  # Leimattu kehitysversiosarja: tulkitaan viimeinen luku indeksinä.
  'refs/tags/v[0-9].*': '''{tunnus}{indeksoitu}''',

  # Leimattu versio: käytetään sellaisenaan.
  'refs/tags/v[0-9][0-9.]*?(?![a-z]+[0-9]*)': '''{tunnus}''',

  # Nollaversio (edeltää ensimmäistä leimaa).
  '0': '0.0',
}

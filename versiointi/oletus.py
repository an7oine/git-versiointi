# pylint: disable=line-too-long

# Huomaa, että `git for-each-ref` ottaa parametrinä `glob(7)`-
# tyyppisen kuvion, ei säännöllistä lauseketta. Tässä määritellystä
# säännöllisestä lausekkeesta annetaan viimeistä vinoviivaa
# edeltävä osa parametrinä em. git-komennolle.
REF = {
  '@irto': r'*',
  '@haara': r'refs/heads/ refs/remotes/origin/',
  '@master_tai_vx': ' '.join((
    r'refs/heads/(master|v-[0-9].*)',
    r'refs/remotes/origin/(master|v-[0-9].*)',
  )),
  '@leima_kehitys': r'refs/tags/v[0-9].*',
  '@leima': r'refs/tags/v[0-9][0-9.]*?(?![a-z]+[0-9]*)',
  '@nolla': r'0',
}


KAYTANTO = {
  # Irtoversio (nk. detached HEAD): lisätään etäisyys.
  '@seuraava_etaisyys': (
    '''{pohja}{int(indeksi)+1 if indeksi else ".1"}.dev{etaisyys}'''
  ),

  # (Muun kuin master-) haaran versio:
  # - <+1 tai .1>.dev<etaisyys>+<haara>
  '@seuraava_etaisyys_tunnus': (
    '''{pohja}{int(indeksi)+1 if indeksi else ".1"}.dev{etaisyys}+{tunnus}'''
  ),
  # - indeksoitu kehitysversio tai .1.dev<etaisyys>+<haara>
  '@kehitys_tai_etaisyys_tunnus': (
    '''{pohja}{int(indeksi)+etaisyys if indeksi else f'.1.dev{etaisyys}+{tunnus}'}'''
  ),

  # Master-haara tai versiohaara (v-X.Y):
  # indeksoitu kehitysversio tai etäisyyden mukainen pääte.
  '@indeksoitu_tai_aliversio': (
    '''{pohja}{int(indeksi)+etaisyys if indeksi else f'.{etaisyys}'}{indeksoitu}'''
  ),

  # Leimattu kehitysversiosarja: tulkitaan viimeinen luku indeksinä.
  '@leima_indeksoitu': '''{tunnus[1:]}{indeksoitu}''',

  # Leimattu (ei-kehitys-) versio: poimitaan tunnus, poistetaan "v".
  # Semver: täydennetään kolmiosaiseksi, indeksoidaan viimeinen segmentti.
  '@leima': '''{tunnus[1:]}''',
  '@leima_semver': (
    '''{(alku := tunnus[1:]) + '.0' * max(0, 2-alku.count('.'))}{indeksoitu}'''
  ),

  # Nollaversio (edeltää ensimmäistä leimaa).
  # Semver: kolmiosainen, indeksoitu.
  '@nolla': '0.0',
  '@nolla_semver': '0.0.0{indeksoitu}',
}


VERSIOKAYTANTO = {
  # Vakiokäytäntö: numerointi seuraa <master>- tai vX-tyyppistä haaraa,
  # muut haarat erotetaan <+1>.dev -tunnuksella ja nimetään (<etaisyys>+<nimi>).
  'oletus': (oletus := {
    REF['@irto']: KAYTANTO['@seuraava_etaisyys'],
    REF['@haara']: KAYTANTO['@seuraava_etaisyys_tunnus'],
    REF['@master_tai_vx']: KAYTANTO['@indeksoitu_tai_aliversio'],
    REF['@leima_kehitys']: KAYTANTO['@leima_indeksoitu'],
    REF['@leima']: KAYTANTO['@leima'],
    REF['@nolla']: KAYTANTO['@nolla'],
  }),

  # Kehitykseen optimoitu käytäntö:
  # kehitysversioiden indeksointi seuraa mitä tahansa haaraa.
  # Muutoin kuten oletus.
  'kehitys': {
    **oletus,
    REF['@haara']: KAYTANTO['@kehitys_tai_etaisyys_tunnus'],
  },

  # Ns. semanttinen versiointi: kaikki (ei-kehitys-) versionumerot ovat kolmiosaisia.
  # Viimeisen segmentin indeksointi seuraa <master>-haaraa.
  # Kehitysversioiden numerointia ei rajata.
  'semver': {
    **oletus,
    REF['@leima']: KAYTANTO['@leima_semver'],
    REF['@nolla']: KAYTANTO['@nolla_semver'],
  }
}

git-versiointi
==============

Työkalupaketti pakettiversion ja -historian sekä vaadittavien riippuvuuksien
automaattiseen määrittämiseen.

# Asennus

Asennusta järjestelmään ei tarvita työasemalla eikä palvelimella.

Työkalut otetaan sen sijaan käyttöön kunkin halutun pip-asennettavan git-projektin osalta muokkaamalla vastaavaa `setup.py`-tiedostoa seuraavasti:
```python
...
setup(
  ...
  setup_requires=['git-versiointi'], # <-- LISÄTÄÄN
  ...
  # version=...                        <-- POISTETAAN
  ...
)
```
Lisäksi voidaan tarvittaessa antaa parametrin `git_versiointi` arvoksi `setup.py`-tiedoston sijainti; oletuksena tämä on `sys.argv[0]`.

Kun pakettia asennetaan joko työasemalla (`python setup.py develop`) tai palvelimella (`pip install ...`), tekee järjestelmä `setup.py`-tiedoston suorittamisen yhteydessä automaattisesti seuraavaa:
* asentaa `git-versiointi`-paketin, ellei sitä löydy jo valmiiksi järjestelmästä
* suorittaa normaalin asennuksen muodostaen versionumeron yms. tiedot automaattisesti (ks. kuvaus jäljempänä)
* poistaa asennuksen ajaksi asennetun `git-versiointi`-paketin

# Versionumeron tutkiminen

Git-versiointia käyttävän paketin versionumero voidaan poimia komentoriviltä seuraavasti:
```bash
python <paketti>/setup.py --version [--ref XXX]
```

Python-kutsulle voidaan antaa parametri `--ref XXX`, missä `XXX` on git-muutoksen tiiviste, haaran tai leiman nimi tms. Tällöin palautetaan versionumero kyseisen muutoksen kohdalla. Mikäli paketin (ali-) versiointikäytäntö on muuttunut annetun revision ja nykyisen tilanteen (`HEAD`) välillä, saattaa ilmoitettu versionumero poiketa historiallisesta, kyseisellä hetkellä silloisen käytännön mukaisesti lasketusta.

# Toimintaperiaate

Skripti asettaa asennettavan python-jakelun tietoihin seuraavat tiedot:
* `version`: versionumero
* `historia`: JSON-data, joka sisältää projektin git-versiohistorian

## Versionumeron muodostus

Versio- ja aliversionumero muodostetaan paketin sisältämän `git`-tietovaraston sisältämien tietojen mukaan. Tietovarastosta etsitään versionumerolta näyttäviä leimoja: tyyppiä `^v[0-9]`.

Mikäli tiettyyn git-muutokseen osoittaa suoraan jokin leima, puhutaan (kokonaisesta) versiosta; muutoin kyseessä on aliversio. Mikäli leima on tyyppiä `[a-z][0-9]*$`, puhutaan kehitysversiosta; muutoin kyseessä on julkaisuversio.

Kokonaisen version numero poimitaan versionumerojärjestyksessä (PEP 440) suurimman, suoraan kyseiseen muutokseen osoittavan git-leiman mukaisesti. Ensisijaisesti haetaan julkaisu- ja toissijaisesti kehitysversiota. Näin löydetty suora versioleima annetaan parametrinä `leima`.

Aliversion numero lasketaan lähimmän, versionumerojärjestyksessä suurimman julkaisu- tai kehitysversion sekä tämän päälle lasketun git-muutoshistorian pituuden mukaan. Nämä tiedot annetaan parametreinä `leima` ja `etaisyys`.

Oletuksena versio- ja aliversionumero lasketaan näiden tietojen mukaan seuraavasti:
* kokonaiseen versioon liittyvän leima sellaisenaan
* jos lähin, viimeisin leima kuvaa kehitysversiota (esim. `v1.2.3a1`, `v1.2.3.dev3`), muodostetaan aliversio lisäämällä etäisyys leiman loppunumeroon, esim. etäisyys 3 -> `v1.2.3a4`, `v1.2.3.dev6`
* muussa tapauksessa aliversion etäisyys lisätään alanumerona leiman kuvaaman versionumero perään, esim. `v1.2` + etäisyys 3 (kolme muutosta) --> versionumero `v1.2.3`

Versionumeroiden määritys voidaan räätälöidä paketin `setup.cfg`-tiedostossa `[versiointi]`-osion sisällä (ks. esimerkki alempana).

Huom. nämä räätälöinnit eivät vaikuta edellä kuvattuun kehitysversioiden numerointiin.

Kaikki oletusarvoiset tai räätälöidyn logiikan mukaan muodostetut versionumerot normalisoidaan lopuksi PEP 440:n mukaisesti.

## Historiatiedot

Paketin tietoihin lisättävä `historia` kirjoitetaan asennetun paketin metatietoihin (`EGG-INFO`) tiedostoon `historia.json`.

Paketin omissa asennustiedoissa määritetty tietue `entry_points[egg_info.writers]` asettaa kirjoituskomennon tiedostolle `historia.json`

# Räätälöity versiointikäytäntö

Määritystiedostossa setup.cfg voidaan asettaa haluttu versiointikäytäntö. Kukin määrityksen rivi vastaa tietyntyyppistä git-viittausta (leima, haara tai paljas revisio) sekä versionumeroa, joka tämäntyyppiselle viittaukselle asetetaan.

Kunkin rivin avainosa tulkitaan (yhtenä tai useampana, välilyönnein erotettuna) säännöllisenä lausekkeena, joka täsmää (pitkään) git-viittaukseen: refs/.../...

Lisäksi tulkitaan seuraavat erityiset avaimet:
* `*`: mikä tahansa revisio
* `0`: git-versiohistoria ennen ensimmäistä leimaa.

Kunkin käytännön arvo-osa tulkitaan python-`f`-merkkijonona (PEP 498), johon täydennetään seuraavat muuttujat:

* pohja: ulomman versiointikäytännön tuottama (annettua viittausta edeltävä) versio
* indeksi: mahdollinen indeksi `pohja`-versioon liittyen
  (esim. ulompi versio v1.2dev3 ==> `pohja=1.2dev`, `indeksi=3`)
* etaisyys: etäisyys annetusta viittauksesta ulomman käytännön mukaiseen pohjaversioon
* tunnus: leiman nimen mukaan poimittu suora versionumero (vain leimattu revisio)
* indeksoitu: merkitse tuloksena syntyvä versionumero indeksoiduksi
  (tällöin indeksi poimitaan versionumeron viimeisten numeroiden mukaan, oletus 0)

Oletuksena käytetään versiointikäytäntöä, joka vastaa seuraavaa määritystä:
```ini
[versiointi]

# Irtoversio: lisätään `+etäisyys`.
*: {pohja}+{etaisyys}

# Mikä tahansa haara: lisätään `+haara.etäisyys`.
refs/heads/ refs/remotes/origin/:
  {pohja}{int(indeksi)+etaisyys if indeksi else f'+{tunnus}.{etaisyys}'}

# v- -alkuinen haara: tulkitaan kuten `master`.
refs/heads/v-[0-9].* refs/remotes/origin/v-[0-9].*:
  {pohja}{int(indeksi)+etaisyys if indeksi else f'.{etaisyys}'}

# master-haara: lisätään pohjaversion indeksiä tai lisätään `.etäisyys`.
refs/heads/master refs/remotes/origin/master:
  {pohja}{int(indeksi)+etaisyys if indeksi else f'.{etaisyys}'}

# Leimattu kehitysversio (v*{a,b,c,dev}*): poimitaan tunnus, indeksoidaan.
refs/tags/v[0-9].*:
  {tunnus}{indeksoitu}

# Leimattu tuotantoversio: poimitaan tunnus sellaisenaan.
refs/tags/v[0-9][0-9.]*?(?![a-z]+[0-9]*):
  {tunnus}

# Historian alku: 0.0.
0:
  0.0
```

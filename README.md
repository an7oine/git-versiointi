git-versiointi
==============

Työkalupaketti pakettiversion ja -historian sekä vaadittavien riippuvuuksien
automaattiseen määrittämiseen.

# Asennus

Asennusta järjestelmään ei tarvita työasemalla eikä palvelimella.

Työkalut otetaan sen sijaan käyttöön kunkin halutun pip-asennettavan git-projektin osalta muokkaamalla vastaavaa `setup.py`-tiedostoa seuraavasti:
```python
import setuptools

setuptools._install_setup_requires({'setup_requires': ['git-versiointi']})
from versiointi import asennustiedot

setuptools.setup(
  ...
  # version=...             <-- POISTA TÄMÄ
  # install_requires=...    <-- POISTA TÄMÄ
  ...
  **asennustiedot(__file__)
)
```

Kun pakettia asennetaan joko työasemalla (`python setup.py develop`) tai palvelimella (`pip install ...`), tekee järjestelmä `setup.py`-tiedoston suorittamisen yhteydessä automaattisesti seuraavaa:
* asentaa `git-versiointi`-paketin, ellei sitä löydy jo valmiiksi järjestelmästä
* suorittaa normaalin asennuksen muodostaen versionumeron yms. tiedot automaattisesti (ks. kuvaus jäljempänä)
* poistaa asennuksen ajaksi asennetun `git-versiointi`-paketin

# Versionumeron tutkiminen

Git-versiointia käyttävän paketin versionumero voidaan poimia komentoriviltä seuraavasti:
```bash
python <paketti>/setup.py --version
```

# Toimintaperiaate

Skripti palauttaa `setup()`-kutsua varten seuraavat parametrit:
* `version`: versionumero
* `historia`: JSON-data, joka sisältää projektin git-versiohistorian
* `install_requires`: asennuksen vaatimat riippuvuudet

## Versionumeron muodostus

Versio- ja aliversionumero muodostetaan paketin sisältämän `git`-tietovaraston sisältämien tietojen mukaan. Tietovarastosta etsitään versionumerolta näyttäviä leimoja: tyyppiä `^v[0-9]`.

Mikäli tiettyyn git-muutokseen osoittaa suoraan jokin leima, puhutaan (kokonaisesta) versiosta; muutoin kyseessä on aliversio. Mikäli leima on tyyppiä `[a-z][0-9]*$`, puhutaan kehitysversiosta; muutoin kyseessä on julkaisuversio.

Kokonaisen version numero poimitaan versionumerojärjestyksessä (PEP 440) suurimman, suoraan kyseiseen muutokseen osoittavan git-leiman mukaisesti. Ensisijaisesti haetaan julkaisu- ja toissijaisesti kehitysversiota. Näin löydetty suora versioleima annetaan parametrinä `leima`.

Aliversion numero lasketaan lähimmän, versionumerojärjestyksessä suurimman julkaisu- tai kehitysversion sekä tämän päälle lasketun git-muutoshistorian pituuden mukaan. Nämä tiedot annetaan parametreinä `leima` ja `etaisyys`.

Oletuksena versio- ja aliversionumero lasketaan näiden tietojen mukaan seuraavasti:
* kokonaiseen versioon liittyvän leima sellaisenaan
* jos lähin, viimeisin leima kuvaa kehitysversiota (esim. `v1.2.3a1`, `v1.2.3.dev3`), muodostetaan aliversio lisäämällä etäisyys leiman loppunumeroon, esim. etäisyys 3 -> `v1.2.3a4`, `v1.2.3.dev6`
* muussa tapauksessa aliversion etäisyys lisätään alanumerona leiman kuvaaman versionumero perään, esim. `v1.2` + etäisyys 3 (kolme muutosta) --> versionumero `v1.2.3`

Versionumeroidan määritys voidaan räätälöidä seuraavilla tavoilla:
* antamalla `asennustiedot()`-funktiokutsulle nimettyinä parametreinä `versio`- ja/tai `aliversio`-funktio, joka saa nimetyt parametrit `leima` ja `etaisyys` ja jonka tulee palauttaa versionumero merkkijonona
* antamalla `asennustiedot()`-funktiokutsulle vastaavat parametrit merkkijonoina. Tällöin merkkijonoihin interpoloidaan edellä mainitut parametrit `str.format`-kutsun avulla.
* määrittämällä em. interpoloitavat merkkijonot paketin `setup.cfg`-tiedostossa `[versiointi]`-osion sisällä.

Huom. nämä räätälöinnit eivät vaikuta edellä kuvattuun kehitysversioiden numerointiin.

Kaikki oletusarvoiset tai räätälöidyn logiikan mukaan muodostetut versionumerot normalisoidaan lopuksi PEP 440:n mukaisesti.

## Historiatiedot

`setup()`-kutsulle annettu `historia`-parametri kirjoitetaan asennetun paketin metatietoihin (`EGG-INFO`) tiedostoon `historia.json`.

Tämä on toteutettu `git-versiointi`-paketin omissa asennustiedoissa seuraavasti:
* `entry_points[distutils.setup_keywords]`: määrittää uuden `setup()`-parametrin `historia`
* `entry_points[egg_info.writers]`: määrittää kirjoituskomennon tiedostolle `historia.json`

## Asennusvaatimukset

Riippuvuudet haetaan `requirements.txt`-tiedostosta seuraavasti:
* normaalit Pypi-paketit sellaisenaan (esim. `numpy>=1.7`)
* git-paketteihin lisätään paketin nimi alkuun
  - esim. `paketti @ git+https://github.com/x/paketti.git`

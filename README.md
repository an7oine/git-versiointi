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

# Toimintaperiaate

Skripti palauttaa `setup()`-kutsua varten seuraavat parametrit:
* `version`: versionumero
* `historia`: JSON-data, joka sisältää projektin git-versiohistorian
* `install_requires`: asennuksen vaatimat riippuvuudet

## Versionumeron muodostus

Versionumero muodostetaan `.git`-hakemiston sisältämien tietojen mukaan:
* viimeisin leima (`git-tag`), josta poistetaan alusta mahdollinen `v`
* mikäli leiman päälle on tehty muutoksia, näiden lukumäärä lisätään alanumerona versionumeron perään:
  - esim. `v1.2` + 3 muutosta --> versionumero `1.2.3`

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

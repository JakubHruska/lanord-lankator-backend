# Lanord Manager - Package Server

Webová backend aplikace (postavená na frameworku Django) primárně určená pro správu velkých datových archivů (např. hry, instalátory, patche). Aplikace balíčky bezpečně ukládá, verifikuje (validace ZIP archivů), generuje k nim manifesty (JSON) a vystavuje je skrze REST API pro klientské stažení. 

Tento repozitář obsahuje backend samotný.

---

## Lokální instalace a spuštění (BEZ Dockeru)

Následující návod ukazuje, jak projekt zprovoznit lokálně pro vývojové účely.

### 1. Prerekvizity
* Nainstalovaný **Python 3.10+**
* Nainstalovaný gigabalíček **pip**
* (Doporučeno) Nástroj pro virtuální prostředí `venv`

### 2. Instalace závislostí a aktivace virtuálního prostředí
Otevřete terminál ve složce projektu (`package_server`) a zadejte:

```bash
# 1. Vytvoření virtuálního prostředí (pouze poprvé)
python -m venv venv

# 2. Aktivace prostředí
# Na Windows (PowerShell/CMD):
venv\Scripts\activate
# Na Linux / Mac:
# source venv/bin/activate

# 3. Instalace balíčků
pip install -r requirements.txt
```

### 3. Vytvoření `.env` souboru
V kořenové složce projektu (tam kde je `manage.py`) vytvořte nový soubor s názvem `.env` a vložte do něj následující obsah.

```dotenv
# .env
DEBUG=True
SECRET_KEY=tvuj-libovolny-tajny-klic-pro-lokalni-vyvoj
ALLOWED_HOSTS=localhost,127.0.0.1
MEDIA_PATH=media
CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```
*Pozn.: Pro lokální vývoj můžete nechat klíč vymyšlený a `DEBUG=True`. Do složky zvolené v `MEDIA_PATH` se začnou tvořit a spravovat archivy.*

### 4. Databáze (Migrace) a vytvoření Admin účtu
Aplikace potřebuje vytvořit prázdnou databázi (výchozí SQLite) a základní tabulky. V terminálu spusťte:

```bash
# Vytvoření tabulek v databázi db.sqlite3
python manage.py migrate

# Vytvoření administrátorského (superuser) účtu
python manage.py createsuperuser
```
*(Během vytváření superusera budete vyzváni k zadání loginu, emailu a hesla. Toto heslo se při psaní nezobrazuje.)*

### 5. Spuštění serveru
Nyní je vše připraveno. Server se startuje příkazem:

```bash
python manage.py runserver
```

Aplikace bude následně dostupná na `http://127.0.0.1:8000/`.
Do administrativního rozhraní se dostanete přes `http://127.0.0.1:8000/admin/`.

---

## Struktura složek pro archivy

Při prvním spuštění a nahrávání dat začne Django používat cestu určenou v proměnné `MEDIA_PATH` (dle `.env` návodu je to repozitářová složka `media/`). Strukturu tvoří následující sekce:

```text
media/
 ├── new/       # Odkládací "čekací" složka pro manuální přenos velkých gigabajtových archivů.
 └── archives/  # Sem si systém balíčky automaticky fyzicky přesouvá a zpracovává k finální publikaci.
     └── <slug_balicku>/
         ├── balicek.zip
         └── manifest.json
```
_Ke kontrole a vytvoření můžete použít ruční mkdir nebo počkat na vytvoření aplikací:_
`mkdir -p media/new media/archives`

---

## Jak přidat nový balíček

Díky architektuře existují dva způsoby nahrání, záleží na preferenci a na tom, obsluhovat velké soubory:

### Způsob A: Webový Upload (Menší soubory)
1. Běžte do administrace (`http://127.0.0.1:8000/admin/`) a přihlaste se.
2. V sekci **Api** najděte a zaklikněte **Balíčky** -> **Přidat**.
3. Vyplňte název, typ, unikátní `slug` (např. `gta-sa-patch`).
4. V poli **ZIP Archiv (upload)** standardně vyberte přes modální okno soubor ve vašem počítači.
5. Uložte (nebo zaškrtněte, jestli je "Publikováno"). Hotovo.

### Způsob B: Vložení ze složky "new" (Velké soubory GB+)
Při nahrávání obřích archivů je mnohem lepší soubor nakopírovat napřímo a vyhnout se timeoutu prohlížeče.
1. Vemte váš ZIP archiv (např. `velkahra.zip`) a fyzicky jej zkopírujte na disku do složky `media/new/`.
2. Běžte do administrace do přidávání nového Balíčku.
3. Vyplňte údaje (název, slug atd.).
4. Místo výběru souboru myší (necháte pole "ZIP Archiv" prázdné) napište do pole **Soubor v /new** pouze přesný _název souboru_, tedy např.: `velkahra.zip`.
5. Uložte záznam.
6. Aplikace si na pozadí automaticky prohledá složku `/new`, překontroluje zda jde o ZIP, změří jeho datovou velikost a **navždy si ho přesune** do složky `media/archives/<tvuj-slug>/`. Vygeneruje k němu navíc `manifest.json`.

# Nasazení – Proxmox VM (10.0.20.240)

## Předpoklady

- Ubuntu 22.04 / 24.04 LTS na VM
- Docker + Docker Compose plugin
- Přístup k Samba síťovému úložišti

---

## 1. Instalace Dockeru na VM

```bash
sudo apt update && sudo apt install -y ca-certificates curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Odhlásit se a přihlásit znovu, aby se projevilo členství ve skupině docker
```

---

## 2. Namontování Samby

```bash
# Instalace cifs-utils
sudo apt install -y cifs-utils

# Vytvoření bodu připojení
sudo mkdir -p /mnt/samba_games

# Jednorázové připojení (pro test)
sudo mount -t cifs //192.168.x.x/games /mnt/samba_games \
  -o username=UZIVATEL,password=HESLO,uid=$(id -u),gid=$(id -g)

# Trvalé připojení přes /etc/fstab (přidej tento řádek):
# //192.168.x.x/games  /mnt/samba_games  cifs  username=UZIVATEL,password=HESLO,uid=1000,gid=1000,iocharset=utf8,_netdev  0  0

# Ověření
ls /mnt/samba_games/_packages
```

> **Důležité:** Složka `_packages` v Samba shareu musí existovat –  
> do ní Django hledá mediální soubory (balíčky her).

---

## 3. Klonování repozitáře

```bash
# SSH klíč musí být přidán do GitHub/GitLab
git clone git@github.com:TVUJ_UZIVATEL/lanord-manager.git
cd lanord-manager/package_server

# Přepnutí na větev dev
git checkout dev
```

---

## 4. Nastavení prostředí (.env)

```bash
cp .env.example .env
nano .env   # nebo: vim .env
```

Minimální produkční `.env`:

```dotenv
DEBUG=False
SECRET_KEY=<vygeneruj: python -c "import secrets; print(secrets.token_urlsafe(50))">
ALLOWED_HOSTS=10.0.20.240,localhost
MEDIA_PATH=/app/media
CORS_ALLOWED_ORIGINS=http://10.0.20.240
```

Generování bezpečného klíče:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 5. Spuštění

```bash
# První build a start
docker compose up -d --build

# Ověření, že kontejnery běží
docker compose ps

# Logy
docker compose logs -f web
docker compose logs -f nginx
```

---

## 6. Ověření funkčnosti

```bash
# API dostupné?
curl http://10.0.20.240/api/

# Balíček dostupný přes Nginx?
curl -I http://10.0.20.240/media/muj_balik.zip
```

---

## Aktualizace aplikace

```bash
git pull origin dev
docker compose up -d --build
```

---

## Struktura volumů

| Host                              | Kontejner          | Účel                        |
|-----------------------------------|--------------------|-----------------------------|
| `/mnt/samba_games/_packages`      | `/app/media`       | Balíčky her (Samba)         |
| `./db.sqlite3`                    | `/app/db.sqlite3`  | SQLite databáze (persistentní) |
| Docker volume `staticfiles`       | `/app/staticfiles` | CSS/JS pro Nginx            |

---

## Řešení problémů

**Samba není dostupná při startu Dockeru:**
```bash
# Ověř, že mount existuje před spuštěním docker compose
ls /mnt/samba_games/_packages
```

**Migrace selhávají:**
```bash
docker compose exec web python manage.py migrate --noinput
```

**Gunicorn nespustí:**
```bash
docker compose logs web
# Zkontroluj SECRET_KEY a ALLOWED_HOSTS v .env
```


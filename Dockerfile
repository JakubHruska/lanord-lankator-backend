FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Systémové závislosti
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python závislosti
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Zkopírování projektu
COPY . /app/

# Entrypoint (jako root – chmod potřebuje root)
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Nastav vlastníka /app na uid 1000, pak přepni uživatele
RUN chown -R 1000:1000 /app

# Vytvoř staticfiles adresář se správným vlastníkem
RUN mkdir -p /app/staticfiles && chown -R 1000:1000 /app/staticfiles

RUN chown -R 1000:1000 /app

USER 1000:1000

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

import json
import os
import filetype

from django.db import models
from django.core.exceptions import ValidationError


def validate_is_zip(file):
    chunk = file.read(2048)
    file.seek(0)  # Vrátit kurzor zpět
    kind = filetype.guess(chunk)
    if kind is None or kind.mime not in ['application/zip', 'application/x-zip-compressed']:
        mime = kind.mime if kind else 'neznámý'
        raise ValidationError(f'Soubor není validní ZIP. Zjištěn typ: {mime}')


def get_upload_path(instance, filename):
    # instance je tvůj objekt Package, filename je původní název souboru
    # Výsledek: media/archives/counter-strike/soubor.zip
    return os.path.join('archives', instance.slug, filename)


class Package(models.Model):
    class Type(models.TextChoices):
        INSTALLER = 'installer', 'Instalátor'
        READY_TO_PLAY = 'ready_to_play', 'Ready to Play'
        PATCH = 'patch', 'Patch / Fix'
        OTHER = 'other', 'Ostatní'

    PACKAGE_TYPE_CHOICES = (
        (Type.INSTALLER, Type.INSTALLER.label),
        (Type.READY_TO_PLAY, Type.READY_TO_PLAY.label),
        (Type.PATCH, Type.PATCH.label),
        (Type.OTHER, Type.OTHER.label),
    )

    # Základní metadata
    title = models.CharField(max_length=255, verbose_name="Název balíčku")
    type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPE_CHOICES,
        default=Type.INSTALLER,
        verbose_name="Typ balíčku",
    )
    slug = models.SlugField(unique=True, help_text="Unikátní identifikátor (např. nazev-app-v1)")
    description = models.TextField(blank=True, verbose_name="Popis balíčku")

    # Cesty k souborům
    archive_file = models.FileField(
        upload_to=get_upload_path,
        verbose_name="ZIP Archiv",
        validators=[validate_is_zip]
    )

    # Metadata z manifestu uložená přímo v DB pro rychlý přístup
    # Vyžaduje PostgreSQL nebo novější SQLite
    manifest_data = models.JSONField(default=dict, blank=True, verbose_name="Data z manifestu")

    # Statistika a info pro klienta
    file_size = models.BigIntegerField(default=0,
                                       help_text="Velikost v bajtech — vyplňuje se automaticky z nahraného souboru.")
    is_published = models.BooleanField(default=False, verbose_name="Publikováno")

    # Časové značky
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Balíček"
        verbose_name_plural = "Balíčky"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"

    def save(self, *args, **kwargs):
        # Aktualizovat velikost souboru pokud existuje (zajistí správný údaj v manifestu)
        if self.archive_file:
            try:
                self.file_size = self.archive_file.size
            except Exception:
                pass

        super().save(*args, **kwargs)

        # Cesta k uloženému souboru
        if self.archive_file:
            file_path = self.archive_file.path
            directory = os.path.dirname(file_path)
            manifest_path = os.path.join(directory, 'manifest.json')

            # Data pro manifest
            manifest_data = {
                "slug": self.slug,
                "type": self.type,
                "title": self.title,
                "description": self.description,
                "file_size": self.file_size,
                "archive_file": os.path.basename(self.archive_file.name),
                "created_at": self.created_at.isoformat() if hasattr(self, 'created_at') else None
            }

            # Zápis do souboru
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=4, ensure_ascii=False)

            # Uložit manifest_data také do DB (použijeme update přes queryset, aby se předešlo rekurzivnímu volání save)
            self.manifest_data = manifest_data
            try:
                type(self).objects.filter(pk=self.pk).update(manifest_data=manifest_data)
            except Exception:
                # pokud update selže, nic dalšího neděláme (možno přidat logging)
                pass

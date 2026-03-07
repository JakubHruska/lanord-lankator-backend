import json
import os
import shutil
import filetype

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


def validate_is_zip(file):
    chunk = file.read(2048)
    file.seek(0)
    kind = filetype.guess(chunk)
    if kind is None or kind.mime not in ['application/zip', 'application/x-zip-compressed']:
        mime = kind.mime if kind else 'neznámý'
        raise ValidationError(f'Soubor není validní ZIP. Zjištěn typ: {mime}')


def get_upload_path(instance, filename):
    return os.path.join('archives', instance.slug, filename)


def get_new_packages_dir():
    return os.path.join(settings.MEDIA_ROOT, 'new')


def get_archives_dir():
    return os.path.join(settings.MEDIA_ROOT, 'archives')


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

    title = models.CharField(max_length=255, verbose_name="Název balíčku")
    type = models.CharField(
        max_length=20,
        choices=PACKAGE_TYPE_CHOICES,
        default=Type.INSTALLER,
        verbose_name="Typ balíčku",
    )
    slug = models.SlugField(unique=True, help_text="Unikátní identifikátor (např. nazev-app-v1)")
    description = models.TextField(blank=True, verbose_name="Popis balíčku")

    archive_file = models.FileField(
        upload_to=get_upload_path,
        verbose_name="ZIP Archiv (upload)",
        validators=[validate_is_zip],
        blank=True,
        null=True,
    )

    # Název souboru umístěného v packages/new/ na serveru
    pending_filename = models.CharField(
        max_length=512,
        blank=True,
        verbose_name="Soubor v /new",
        help_text="Název ZIP souboru umístěného ve složce packages/new/ na serveru (např. hra.zip). "
                  "Po uložení se soubor přesune do archives/<slug>/."
    )

    manifest_data = models.JSONField(default=dict, blank=True, verbose_name="Data z manifestu")
    file_size = models.BigIntegerField(default=0,
                                       help_text="Velikost v bajtech — vyplňuje se automaticky.")
    is_published = models.BooleanField(default=False, verbose_name="Publikováno")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Balíček"
        verbose_name_plural = "Balíčky"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_type_display()})"

    def _process_pending_file(self):
        """
        Vezme soubor z packages/new/, validuje ho, přesune do packages/archives/<slug>/
        a vrátí absolutní cestu k přesunutému souboru.
        """
        src = os.path.join(get_new_packages_dir(), self.pending_filename)

        if not os.path.isfile(src):
            raise FileNotFoundError(f'Soubor nebyl nalezen ve složce /new: {src}')

        with open(src, 'rb') as f:
            chunk = f.read(2048)
        kind = filetype.guess(chunk)
        if kind is None or kind.mime not in ['application/zip', 'application/x-zip-compressed']:
            raise ValidationError(f'Soubor není validní ZIP.')

        dest_dir = os.path.join(get_archives_dir(), self.slug)
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, self.pending_filename)

        shutil.move(src, dest)
        return dest

    def save(self, *args, **kwargs):
        resolved_path = None

        # Priorita 1: soubor čeká v /new
        if self.pending_filename:
            dest = self._process_pending_file()
            self.file_size = os.path.getsize(dest)
            # Uložit relativní cestu do archive_file (relativně k MEDIA_ROOT)
            self.archive_file = os.path.relpath(dest, settings.MEDIA_ROOT).replace('\\', '/')
            self.pending_filename = ''  # Vymazat — soubor je přesunut
            resolved_path = dest

        # Priorita 2: klasický upload přes prohlížeč
        elif self.archive_file:
            try:
                self.file_size = self.archive_file.size
                resolved_path = self.archive_file.path
            except Exception:
                pass

        super().save(*args, **kwargs)

        # Generovat manifest.json vedle ZIP souboru
        if resolved_path and os.path.isfile(resolved_path):
            directory = os.path.dirname(resolved_path)
            manifest_path = os.path.join(directory, 'manifest.json')

            manifest_data = {
                "slug": self.slug,
                "type": self.type,
                "title": self.title,
                "description": self.description,
                "file_size": self.file_size,
                "archive_file": os.path.basename(resolved_path),
                "created_at": self.created_at.isoformat() if self.created_at else None
            }

            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=4, ensure_ascii=False)

            self.manifest_data = manifest_data
            try:
                type(self).objects.filter(pk=self.pk).update(
                    manifest_data=manifest_data,
                    archive_file=self.archive_file.name if self.archive_file else '',
                    pending_filename='',
                    file_size=self.file_size,
                )
            except Exception:
                pass

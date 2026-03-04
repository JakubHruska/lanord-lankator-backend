from django.db import models


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

    # Cesty k souborům (relativní k MEDIA_ROOT)
    # FileField v Djangu automaticky zvládá generování URL
    archive_file = models.FileField(upload_to='archives/', verbose_name="ZIP Archiv")

    # Metadata z manifestu uložená přímo v DB pro rychlý přístup
    # Vyžaduje PostgreSQL nebo novější SQLite
    manifest_data = models.JSONField(default=dict, blank=True, verbose_name="Data z manifestu")

    # Statistika a info pro klienta
    file_size = models.BigIntegerField(default=0, help_text="Velikost v bajtech")
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
        # Tady můžeme v budoucnu přidat automatický výpočet velikosti souboru
        if self.archive_file and not self.file_size:
            try:
                self.file_size = self.archive_file.size
            except:
                pass
        super().save(*args, **kwargs)
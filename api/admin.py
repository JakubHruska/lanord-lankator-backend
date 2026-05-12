import os
from django import forms
from django.contrib import admin
from django.conf import settings
from .models import Package


def get_pending_file_choices():
    """Vrátí seznam ZIP souborů dostupných v packages/new/ na serveru."""
    new_dir = os.path.join(settings.MEDIA_ROOT, 'new')
    if not os.path.isdir(new_dir):
        return [('', '--- složka /new neexistuje ---')]
    files = [f for f in os.listdir(new_dir) if f.lower().endswith('.zip')]
    choices = [('', '--- vyberte soubor ze serveru ---')]
    choices += [(f, f) for f in sorted(files)]
    return choices


class PackageAdminForm(forms.ModelForm):
    type = forms.ChoiceField(
        choices=[('', '-- Vyberte typ --')] + list(Package.PACKAGE_TYPE_CHOICES),
        label="Typ balíčku",
    )

    pending_filename = forms.ChoiceField(
        choices=[],
        required=False,
        label="Soubor v /new",
        help_text="ZIP soubory dostupné ve složce packages/new/ na serveru. "
                  "Po uložení se soubor přesune do archives/&lt;slug&gt;/.",
    )

    class Meta:
        model = Package
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Načíst aktuální soubory při každém otevření formuláře
        self.fields['pending_filename'].choices = get_pending_file_choices()

    def clean(self):
        cleaned = super().clean()
        pending = cleaned.get('pending_filename')
        archive = cleaned.get('archive_file')
        # Při vytvoření musí být zadán alespoň jeden zdroj
        if not self.instance.pk and not pending and not archive:
            raise forms.ValidationError(
                'Musíš vybrat soubor ze serveru (/new) nebo nahrát ZIP archiv.'
            )
        return cleaned


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageAdminForm
    list_display = ('title', 'type', 'slug', 'file_size', 'is_published', 'created_at')
    list_filter = ('type', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('file_size', 'manifest_data', 'created_at', 'updated_at')
    fields = (
        'title', 'type', 'slug', 'description',
        'pending_filename',
        'archive_file',
        'file_size', 'manifest_data',
        'is_published',
        'created_at', 'updated_at',
    )

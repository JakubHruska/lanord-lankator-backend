from django import forms
from django.contrib import admin
from .models import Package


class PackageAdminForm(forms.ModelForm):
    type = forms.ChoiceField(
        choices=[('', '-- Vyberte typ --')] + list(Package.PACKAGE_TYPE_CHOICES),
        label="Typ balíčku",
    )

    class Meta:
        model = Package
        fields = '__all__'


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    form = PackageAdminForm
    list_display = ('title', 'type', 'is_published', 'created_at')
    list_filter = ('type', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('file_size',)
    fields = ('title', 'type', 'slug', 'description', 'archive_file', 'file_size', 'manifest_data', 'is_published')

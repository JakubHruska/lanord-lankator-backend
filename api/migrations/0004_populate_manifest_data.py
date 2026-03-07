from django.db import migrations
import json
import os


def generate_manifest_data(apps, schema_editor):
    Package = apps.get_model('api', 'Package')
    for pkg in Package.objects.all():
        manifest = {
            "slug": pkg.slug,
            "type": pkg.type,
            "title": pkg.title,
            "description": pkg.description,
            "file_size": pkg.file_size,
            "archive_file": os.path.basename(pkg.archive_file.name) if pkg.archive_file else None,
            "created_at": pkg.created_at.isoformat() if pkg.created_at else None,
        }
        pkg.manifest_data = manifest
        # Použijeme update přes queryset, aby se předešlo volání save() s vlastním zápisem souboru
        Package.objects.filter(pk=pkg.pk).update(manifest_data=manifest)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_package_archive_file_alter_package_file_size'),
    ]

    operations = [
        migrations.RunPython(generate_manifest_data, reverse_code=migrations.RunPython.noop),
    ]


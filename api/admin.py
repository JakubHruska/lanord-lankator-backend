from django.contrib import admin
from .models import Package

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'is_published', 'created_at')
    list_filter = ('type', 'is_published')
    prepopulated_fields = {'slug': ('title',)}
    fields = ('title', 'type', 'slug', 'description', 'archive_file', 'file_size', 'manifest_data', 'is_published')

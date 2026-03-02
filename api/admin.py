from django.contrib import admin
from .models import Package

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'version', 'is_published', 'created_at')
    prepopulated_fields = {'slug': ('title',)} # Automaticky generuje slug z názvu
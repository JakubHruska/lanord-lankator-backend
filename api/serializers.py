from rest_framework import serializers
from .models import Package


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ['id', 'title', 'type', 'slug', 'description', 'archive_file', 'file_size', 'manifest_data']


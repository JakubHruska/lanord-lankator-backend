from django.urls import path
from .views import PackageListView

urlpatterns = [
    path('packages/', PackageListView.as_view(), name='package-list'),
]

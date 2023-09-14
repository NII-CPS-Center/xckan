"""conf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path

from sites.views import SiteIndexView, SiteSettingIndexView, \
    SiteSettingDetailView, package_list, package_show, \
    package_search, hot_tag, stat, site_validator, site_import, site_export

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SiteIndexView.as_view(), name="home"),
    path('sites/', SiteSettingIndexView.as_view(), name="index"),
    path('sites/import', site_import, name="site-import"),
    path('sites/export', site_export, name="site-export"),
    path('sites/<int:pk>/', SiteSettingDetailView.as_view(), name="site-detail"),
    path('sites/<int:pk>/validate', site_validator, name='site-validate'),
    path('api/package_list', package_list, name='package_list'),
    path('api/package_show', package_show, name='package_show'),
    path('api/package_search', package_search, name='package_search'),
    path('api/hot_tag', hot_tag, name='hot_tag'),
    path('api/stat', stat, name='stat'),
]

# Serving static files during development
# https://docs.djangoproject.com/en/3.2/howto/static-files/#serving-static-files-during-development

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
        + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

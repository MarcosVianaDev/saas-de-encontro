from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import include, path, re_path
from .views import health

admin.site.site_header = "SaaS de Encontro"
admin.site.site_title = "Administração"
admin.site.index_title = "Administração da plataforma"
urlpatterns = [path("admin/", admin.site.urls), path("api/health/", health), path("api/", include("api.urls"))]
if settings.DEBUG:
    urlpatterns += [re_path(r"^static/(?P<path>.*)$", serve)]

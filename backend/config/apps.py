from django.contrib.admin.apps import AdminConfig


class SecureAdminConfig(AdminConfig):
    default_site = 'config.admin_site.SecureAdminSite'

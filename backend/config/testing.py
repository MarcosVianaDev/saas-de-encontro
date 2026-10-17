from unittest import TextTestResult

from django.core.cache import caches
from django.test import override_settings, TransactionTestCase
from django.db import connection
from django.test.runner import DiscoverRunner


class DisposableTransactionTestCase(TransactionTestCase):
    def _fixture_teardown(self):
        if connection.vendor != 'postgresql':
            return super()._fixture_teardown()
        # Only the disposable test DB may flush immutable audit records.
        self.assertTrue(connection.settings_dict['NAME'].startswith('test_'))
        with connection.cursor() as cursor:
            cursor.execute('ALTER TABLE audit_auditlog DISABLE TRIGGER audit_no_truncate')
        try:
            super()._fixture_teardown()
        finally:
            with connection.cursor() as cursor:
                cursor.execute('ALTER TABLE audit_auditlog ENABLE TRIGGER audit_no_truncate')


class IsolatedCacheTestRunner(DiscoverRunner):
    """Exercise throttles without sharing counters with other tests or live Redis."""

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self.cache_settings = override_settings(MEDIA_USE_X_ACCEL_REDIRECT=False, CHANNEL_LAYERS={"default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }}, CACHES={"default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "eventconnect-tests",
        }})
        self.cache_settings.enable()
        self.test_cache = caches['default']

    def teardown_test_environment(self, **kwargs):
        try:
            self.cache_settings.disable()
        finally:
            super().teardown_test_environment(**kwargs)

    def get_resultclass(self):
        base = super().get_resultclass() or TextTestResult
        test_cache = self.test_cache

        class IsolatedCacheResult(base):
            def startTest(self, test):
                # This is the isolated in-memory cache, never the live Redis DB.
                test_cache.clear()
                super().startTest(test)

        return IsolatedCacheResult

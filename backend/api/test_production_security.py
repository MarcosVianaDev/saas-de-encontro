import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient


def production_settings(**changes):
    environment = {**os.environ, 'DJANGO_DEBUG': '0'}
    for key in ['DJANGO_ALLOWED_HOSTS', 'DJANGO_CSRF_TRUSTED_ORIGINS', 'DJANGO_TRUST_PROXY_SSL_HEADER']:
        environment.pop(key, None)
    environment.update(changes)
    path = Path(__file__).resolve().parents[1] / 'config/settings/__init__.py'
    with patch.dict(os.environ, environment, clear=True):
        return runpy.run_path(str(path))


class ProductionSettingsTests(SimpleTestCase):
    def test_production_requires_hosts_instead_of_wildcard_fallback(self):
        with self.assertRaises(ImproperlyConfigured):
            production_settings()
        for hosts in ['', ' , ', '*', 'app.example.com,*', '*.example.com']:
            with self.subTest(hosts=hosts), self.assertRaises(ImproperlyConfigured):
                production_settings(DJANGO_ALLOWED_HOSTS=hosts)

    def test_production_enables_secure_cookies_and_https(self):
        config = production_settings(DJANGO_ALLOWED_HOSTS=' app.example.com, api.example.com, ')
        self.assertEqual(config['ALLOWED_HOSTS'], ['app.example.com', 'api.example.com'])
        for setting in ['SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'SECURE_SSL_REDIRECT']:
            self.assertIs(config[setting], True)
        self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], [])
        self.assertEqual(config['SECURE_PROXY_SSL_HEADER'], ('HTTP_X_FORWARDED_PROTO', 'https'))

    def test_direct_https_deployment_can_disable_proxy_header_trust(self):
        config = production_settings(DJANGO_ALLOWED_HOSTS='app.example.com', DJANGO_TRUST_PROXY_SSL_HEADER='0')
        self.assertIsNone(config['SECURE_PROXY_SSL_HEADER'])
        self.assertTrue(config['SECURE_SSL_REDIRECT'])

    def test_development_keeps_local_http_and_explicit_wildcard_option(self):
        config = production_settings(DJANGO_DEBUG='1')
        self.assertIn('localhost', config['ALLOWED_HOSTS'])
        self.assertNotIn('*', config['ALLOWED_HOSTS'])
        for setting in ['SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'SECURE_SSL_REDIRECT']:
            self.assertIs(config[setting], False)
        self.assertEqual(production_settings(DJANGO_DEBUG='1', DJANGO_ALLOWED_HOSTS='*')['ALLOWED_HOSTS'], ['*'])


@override_settings(
    DEBUG=False, ALLOWED_HOSTS=['app.example.com'],
    SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True, SECURE_SSL_REDIRECT=True,
    SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
)
class ProductionHttpTests(TestCase):
    def test_http_redirects_and_https_proxy_does_not_loop(self):
        client = APIClient()
        response = client.get('/api/session/', HTTP_HOST='app.example.com')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], 'https://app.example.com/api/session/')
        response = client.get('/api/session/', HTTP_HOST='app.example.com', HTTP_X_FORWARDED_PROTO='https')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies['csrftoken']['secure'])

    def test_unknown_host_is_rejected_even_over_https(self):
        self.assertEqual(APIClient().get('/api/session/', secure=True, HTTP_HOST='attacker.example').status_code, 400)

    def test_login_sets_both_secure_cookies_and_keeps_csrf_required(self):
        user = get_user_model().objects.create_user(
            username='production@example.com', email='production@example.com',
            password='Production-test-password-2026!', is_superuser=True,
        )
        client = APIClient(enforce_csrf_checks=True)
        payload = {'email': user.email, 'password': 'Production-test-password-2026!'}
        response = client.post('/api/auth/login/', payload, format='json', secure=True, HTTP_HOST='app.example.com')
        self.assertEqual(response.status_code, 403)
        token = client.get('/api/session/', secure=True, HTTP_HOST='app.example.com').json()['csrfToken']
        response = client.post('/api/auth/login/', payload, format='json', secure=True,
                               HTTP_HOST='app.example.com', HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='https://app.example.com')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.cookies['sessionid']['secure'])
        self.assertTrue(response.cookies['sessionid']['httponly'])
        self.assertTrue(response.cookies['csrftoken']['secure'])

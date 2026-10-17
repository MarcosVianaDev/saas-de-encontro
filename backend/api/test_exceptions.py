from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import path
from rest_framework.exceptions import ValidationError as ApiValidationError
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.organizations.models import Organization
from .exceptions import exception_handler


class ModelValidationView(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = []

    @transaction.atomic
    def post(self, request):
        Organization.objects.create(name='Must roll back')
        raise ValidationError({'name': ['Invalid name.'], 'email': ['Invalid email.']})


urlpatterns = [path('model-validation/', ModelValidationView.as_view())]


class ExceptionHandlerTests(TestCase):
    def test_model_errors_keep_fields_and_all_messages(self):
        response = exception_handler(ValidationError({
            'bio': ['Too short.', 'Required.'], 'name': ['Invalid name.'],
        }), {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'bio': ['Too short.', 'Required.'], 'name': ['Invalid name.']})

    def test_model_error_parameters_are_resolved(self):
        error = ValidationError({'bio': ValidationError('At most %(limit)s characters.', params={'limit': 200})})
        self.assertEqual(exception_handler(error, {}).data, {'bio': ['At most 200 characters.']})

    def test_non_field_errors_keep_all_messages(self):
        self.assertEqual(exception_handler(ValidationError(['First.', 'Second.']), {}).data,
                         {'non_field_errors': ['First.', 'Second.']})

    def test_model_error_marks_atomic_requests_for_rollback(self):
        with patch('api.exceptions.set_rollback') as rollback:
            exception_handler(ValidationError({'bio': 'Invalid.'}), {})
        rollback.assert_called_once_with()

    def test_drf_validation_errors_keep_their_contract(self):
        response = exception_handler(ApiValidationError({'bio': ['Invalid.']}), {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'bio': ['Invalid.']})

    def test_unexpected_errors_are_logged_without_exposing_details(self):
        with self.assertLogs('api.exceptions', level='ERROR'):
            response = exception_handler(RuntimeError('sensitive internal detail'), {})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('sensitive internal detail', str(response.data))

    @override_settings(ROOT_URLCONF=__name__)
    def test_http_response_preserves_fields_and_rolls_back(self):
        response = APIClient().post('/model-validation/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'name': ['Invalid name.'], 'email': ['Invalid email.']})
        self.assertFalse(Organization.objects.filter(name='Must roll back').exists())

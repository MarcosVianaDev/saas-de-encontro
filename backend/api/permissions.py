from rest_framework.permissions import IsAuthenticated
from common.security import request_account_allowed


class AccountAccess(IsAuthenticated):
    message = 'Sua conta está suspensa.'

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request_account_allowed(request)

from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import ScopedRateThrottle


class WriteScopedRateThrottle(ScopedRateThrottle):
    """Keep read polling outside the stricter write budget of each feature."""

    def allow_request(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)

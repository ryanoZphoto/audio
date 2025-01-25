"""
Middleware package for the application.
Contains middleware components for request/response processing.
"""

from .analytics import AnalyticsMiddleware

__all__ = ['AnalyticsMiddleware'] 
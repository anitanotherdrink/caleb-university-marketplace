"""Domain exceptions shared across services (PRD §8.1 error column)."""
from __future__ import annotations


class ServiceError(Exception):
    """Base for all expected, user-surfaceable service errors."""


class DuplicateEmail(ServiceError): ...


class InvalidDomain(ServiceError): ...


class BadCredentials(ServiceError): ...


class NotVerified(ServiceError): ...


class RateLimited(ServiceError): ...


class TokenInvalid(ServiceError): ...


class TokenExpired(ServiceError): ...


class Forbidden(ServiceError): ...


class NotFound(ServiceError): ...


class ImageRejected(ServiceError): ...


class Unavailable(ServiceError): ...


class EmptyCart(ServiceError): ...


class IllegalTransition(ServiceError): ...


class InUse(ServiceError): ...

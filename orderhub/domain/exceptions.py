"""Errores de negocio. Los adaptadores los traducen a su propio protocolo (p. ej. códigos HTTP)."""


class DomainError(Exception):
    """Base de todos los errores de negocio."""

    message = "Error de negocio"

    def __init__(self, message=None):
        super().__init__(message or self.message)
        self.message = message or self.message


class InvalidCredentials(DomainError):
    message = "Credenciales inválidas"


class ProductNotFound(DomainError):
    message = "Producto no encontrado"


class InsufficientStock(DomainError):
    message = "Stock insuficiente"


class InvalidInput(DomainError):
    message = "Datos de entrada inválidos"

"""Errores de negocio. Los adaptadores los traducen a su propio protocolo (p. ej. códigos HTTP)."""


class DomainError(Exception):
    """Base de todos los errores de negocio."""

    message = "Error de negocio"

    def __init__(self, message=None):
        """Usa `message` si se indica; si no, el mensaje por defecto de la clase."""
        super().__init__(message or self.message)
        self.message = message or self.message


class InvalidCredentials(DomainError):
    """Usuario o contraseña incorrectos."""

    message = "Credenciales inválidas"


class InvalidToken(DomainError):
    """Token de sesión ausente, mal formado, con firma inválida o expirado."""

    message = "Token inválido o expirado"


class AccessDenied(DomainError):
    """El usuario está autenticado pero no tiene el rol necesario."""

    message = "Acceso denegado: se requiere rol admin"


class UserAlreadyExists(DomainError):
    """Ya existe un usuario con ese nombre."""

    message = "El nombre de usuario ya está registrado"


class ProductNotFound(DomainError):
    """El producto solicitado no existe."""

    message = "Producto no encontrado"


class InsufficientStock(DomainError):
    """No hay unidades suficientes para la cantidad pedida."""

    message = "Stock insuficiente"


class InvalidInput(DomainError):
    """Los datos de entrada no cumplen las reglas de negocio."""

    message = "Datos de entrada inválidos"

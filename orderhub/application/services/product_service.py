"""Casos de uso del catálogo de productos (RF-01.4, RF-02.1)."""

from typing import Callable, List

from orderhub.application.ports.unit_of_work import UnitOfWork
from orderhub.domain.entities import Product


class ProductService:
    """Gestiona el catálogo. La restricción por rol la aplica el adaptador web
    (@admin_required).
    """

    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        """Recibe la fábrica de Unit of Work por constructor (Dependency Injection)."""
        self._uow_factory = uow_factory

    def create_product(self, name: str, price: float, stock: int) -> Product:
        """Valida y registra un producto nuevo; lanza InvalidInput si los datos no son
        válidos.
        """
        product = Product.create(name, price, stock)
        with self._uow_factory() as uow:
            product = uow.products.add(product)
            uow.commit()
        return product

    def list_products(self) -> List[Product]:
        """Devuelve el catálogo completo con el stock actual de cada producto."""
        with self._uow_factory() as uow:
            return uow.products.list_all()

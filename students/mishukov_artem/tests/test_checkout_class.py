import json

import pytest

from shop.exceptions import InvalidOrderError, OutOfStockError


class TestCheckoutFlow:
    """Сквозные проверки оформления и отмены."""

    def test_checkout_reduces_stock(self, service):
        service.add_to_cart("P001", 2)
        service.checkout()
        assert service.catalog.get("P001").stock == 1

    def test_checkout_persists_order_with_price_snapshot(self, service, repo):
        service.add_to_cart("P001", 1)
        service.checkout()
        raw = json.loads(repo.orders_path.read_text(encoding="utf-8"))
        order = raw["orders"][0]
        assert order["status"] == "new"
        assert order["items"][0]["price"] == 1000.0

    def test_checkout_clears_cart_and_promo(self, service):
        service.add_to_cart("P001", 1)
        service.apply_promo("SALE10")
        service.checkout()
        assert not service.cart
        assert service.cart.promo_code is None

    def test_checkout_increments_order_id(self, service):
        service.add_to_cart("P001", 1)
        service.checkout()
        service.add_to_cart("P002", 1)
        order2 = service.checkout()
        assert order2.id == 2

    def test_checkout_atomic_on_shortage(self, service, repo):
        service.add_to_cart("P001", 3)
        # Искусственно уменьшаем склад — заказ не должен пройти
        service.catalog.get("P001").stock = 1
        with pytest.raises(OutOfStockError):
            service.checkout()
        # Склад не тронут
        assert service.catalog.get("P001").stock == 1
        # И заказ не создан
        raw = json.loads(repo.orders_path.read_text(encoding="utf-8"))
        assert raw["orders"] == []

    def test_checkout_atomic_across_multiple_positions(self, service):
        service.add_to_cart("P001", 1)   # есть
        service.add_to_cart("P002", 2)   # хватит только на 1
        service.catalog.get("P002").stock = 1
        with pytest.raises(OutOfStockError):
            service.checkout()
        # Первая позиция тоже не списана
        assert service.catalog.get("P001").stock == 3

    def test_cancel_returns_stock(self, service):
        service.add_to_cart("P001", 2)
        order = service.checkout()
        assert service.catalog.get("P001").stock == 1
        service.cancel_order(order.id)
        assert service.catalog.get("P001").stock == 3

    def test_cancel_sets_status_cancelled(self, service):
        service.add_to_cart("P001", 1)
        order = service.checkout()
        service.cancel_order(order.id)
        assert service.get_order(order.id).status == "cancelled"

    def test_cancel_twice_raises(self, service):
        service.add_to_cart("P001", 1)
        order = service.checkout()
        service.cancel_order(order.id)
        with pytest.raises(InvalidOrderError):
            service.cancel_order(order.id)

    def test_cancel_unknown_order_raises(self, service):
        with pytest.raises(InvalidOrderError):
            service.cancel_order(999)
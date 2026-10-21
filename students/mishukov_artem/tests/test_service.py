import json

import pytest

from shop.exceptions import (
    EmptyCartError,
    InvalidOrderError,
    InvalidPromoError,
    OutOfStockError,
    ProductNotFoundError,
)


def test_service_add_persists_to_orders_json(service, repo):
    service.add_to_cart("P001", 2)
    raw = json.loads(repo.orders_path.read_text(encoding="utf-8"))
    assert raw["cart"]["items"] == [{"product_id": "P001", "qty": 2}]


def test_service_add_unknown_product_raises(service):
    with pytest.raises(ProductNotFoundError):
        service.add_to_cart("P999", 1)


def test_service_promo_unknown_raises(service):
    with pytest.raises(InvalidPromoError):
        service.apply_promo("NOPE")


def test_service_promo_below_threshold_raises(service):
    service.add_to_cart("P001", 1)  # 1000 < 3000
    with pytest.raises(InvalidPromoError):
        service.apply_promo("MINUS500")


def test_service_promo_replaces_previous(service):
    service.add_to_cart("P001", 1)
    service.apply_promo("SALE10")
    assert service.cart.promo_code == "SALE10"
    service.apply_promo("PUZZLE15")   # валидации нет — применяется всегда
    assert service.cart.promo_code == "PUZZLE15"


def test_service_checkout_empty_cart_raises(service):
    with pytest.raises(EmptyCartError):
        service.checkout()


def test_service_restock_increases_stock(service):
    service.restock("P001", 5)
    assert service.catalog.get("P001").stock == 8


def test_service_restock_unknown_raises(service):
    with pytest.raises(ProductNotFoundError):
        service.restock("P999", 5)


def test_service_get_order_unknown_raises(service):
    with pytest.raises(InvalidOrderError):
        service.get_order(999)


def test_service_export_orders_writes_csv(service, tmp_path):
    service.add_to_cart("P001", 1)
    service.checkout()
    path = tmp_path / "out" / "orders.csv"
    service.export_orders(path)
    content = path.read_text(encoding="utf-8")
    assert "id;status;items_count;subtotal;discount;total" in content
    assert "1;new;1;1000.00;0.00;1000.00" in content
from decimal import Decimal

import pytest

from shop.exceptions import EmptyCartError, ProductNotFoundError


def test_cart_add_creates_item(cart):
    cart.add("P001", 1)
    assert len(cart) == 1


def test_cart_repeat_add_increases_quantity(cart):
    cart.add("P001", 1)
    cart.add("P001", 2)
    assert len(cart) == 1
    assert cart.items[0].qty == 3


def test_cart_add_unknown_product_raises(cart):
    with pytest.raises(ProductNotFoundError):
        cart.add("P999", 1)


def test_cart_remove_missing_raises(cart):
    with pytest.raises(ProductNotFoundError):
        cart.remove("P999")


def test_cart_dunders_len_iter_contains_bool(cart):
    assert not cart
    cart.add("P001", 1)
    assert cart
    assert "P001" in cart
    assert [it.product_id for it in cart] == ["P001"]


def test_cart_subtotal_sums_lines(cart):
    cart.add("P001", 2)                       # 2000
    cart.add("P010", Decimal("0.5"))          # 1200
    assert cart.subtotal() == Decimal("3200.00")


def test_cart_require_non_empty_raises(cart):
    with pytest.raises(EmptyCartError):
        cart.require_non_empty()


def test_cart_clear_resets_items_and_promo(cart):
    cart.add("P001", 1)
    cart.promo_code = "SALE10"
    cart.clear()
    assert not cart
    assert cart.promo_code is None
    assert cart.promo is None
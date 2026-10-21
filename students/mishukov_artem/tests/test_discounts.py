from decimal import Decimal

import pytest

from shop.discounts import (
    CategoryPercentDiscount,
    FixedDiscount,
    PercentDiscount,
    ThreeForTwoDiscount,
)
from shop.exceptions import InvalidPromoError


def test_percent_discount_takes_ten_percent(cart):
    cart.add("P001", 2)  # 2000
    d = PercentDiscount("SALE10", 10)
    assert d.apply(cart) == Decimal("200.00")


def test_fixed_discount_below_threshold_raises(cart):
    cart.add("P001", 1)  # 1000 < 3000
    d = FixedDiscount("MINUS500", 500, 3000)
    with pytest.raises(InvalidPromoError):
        d.validate(cart)
    # и в apply возвращает 0
    assert d.apply(cart) == Decimal("0")


def test_fixed_discount_above_threshold_applies(cart):
    cart.add("P001", 3)  # 3000
    d = FixedDiscount("MINUS500", 500, 3000)
    d.validate(cart)
    assert d.apply(cart) == Decimal("500.00")


def test_fixed_discount_never_goes_negative(cart):
    cart.add("P001", 3)  # 3000 < 10000
    d = FixedDiscount("BIG", 10000, 1000)
    assert d.apply(cart) == Decimal("3000.00")


def test_three_for_two_requires_three_items(cart):
    cart.add("P001", 2)  # только 2 штучных в категории
    d = ThreeForTwoDiscount("BOARD3", "boardgames")
    with pytest.raises(InvalidPromoError):
        d.validate(cart)


def test_three_for_two_makes_cheapest_free(cart):
    cart.add("P001", 1)  # 1000
    cart.add("P002", 2)  # 2 × 500
    d = ThreeForTwoDiscount("BOARD3", "boardgames")
    assert d.apply(cart) == Decimal("500.00")


def test_three_for_two_skips_other_categories(cart):
    cart.add("P004", 3)  # категория puzzles, не boardgames
    d = ThreeForTwoDiscount("BOARD3", "boardgames")
    with pytest.raises(InvalidPromoError):
        d.validate(cart)


def test_category_percent_only_affects_target_category(cart):
    cart.add("P004", 2)   # 800 — puzzles
    cart.add("P001", 1)   # 1000 — boardgames (не должно учитываться)
    d = CategoryPercentDiscount("PUZZLE15", "puzzles", 15)
    assert d.apply(cart) == Decimal("120.00")
from decimal import Decimal

import pytest

from shop.exceptions import InvalidQuantityError, OutOfStockError
from shop.products import DigitalProduct, PieceProduct, WeightProduct


class TestPieceProduct:
    def test_piece_line_price_multiplies_by_quantity(self):
        p = PieceProduct("P1", "X", "c", 100, 10)
        assert p.line_price(3) == Decimal("300.00")

    def test_piece_check_qty_rejects_float(self):
        p = PieceProduct("P1", "X", "c", 100, 10)
        with pytest.raises(InvalidQuantityError):
            p.check_qty(1.5)

    def test_piece_check_qty_rejects_zero_and_negative(self):
        p = PieceProduct("P1", "X", "c", 100, 10)
        with pytest.raises(InvalidQuantityError):
            p.check_qty(0)
        with pytest.raises(InvalidQuantityError):
            p.check_qty(-1)

    def test_piece_check_qty_raises_out_of_stock(self):
        p = PieceProduct("P1", "X", "c", 100, 2)
        with pytest.raises(OutOfStockError):
            p.check_qty(3)

    def test_piece_deduct_reduces_stock(self):
        p = PieceProduct("P1", "X", "c", 100, 5)
        p.deduct(2)
        assert p.stock == 3

    def test_piece_negative_stock_forbidden(self):
        with pytest.raises(ValueError):
            PieceProduct("P1", "X", "c", 100, -1)

    def test_piece_zero_price_forbidden(self):
        with pytest.raises(ValueError):
            PieceProduct("P1", "X", "c", 0, 10)


class TestWeightProduct:
    def test_weight_product_rounds_line_price_to_kopecks(self):
        # 0.35 кг × 2400 ₽/кг = 840.00
        p = WeightProduct("P1", "X", "c", 2400, 0.1, 5)
        assert p.line_price(0.35) == Decimal("840.00")

    def test_weight_line_price_rounds_half_up(self):
        # 100 × 0.333 = 33.30 (ровно после округления до копеек)
        p = WeightProduct("P1", "X", "c", 100, 0.1, 5)
        assert p.line_price(Decimal("0.333")) == Decimal("33.30")

    def test_weight_check_qty_rejects_below_min(self):
        p = WeightProduct("P1", "X", "c", 1000, 0.1, 1.0)
        with pytest.raises(InvalidQuantityError):
            p.check_qty(0.05)

    def test_weight_check_qty_raises_out_of_stock(self):
        p = WeightProduct("P1", "X", "c", 1000, 0.1, 1.0)
        with pytest.raises(OutOfStockError):
            p.check_qty(2.0)

    def test_weight_deduct_reduces_stock_kg(self):
        p = WeightProduct("P1", "X", "c", 1000, 0.1, 2.0)
        p.deduct(Decimal("0.5"))
        assert p.stock_kg == Decimal("1.5")


class TestDigitalProduct:
    def test_digital_line_price(self):
        p = DigitalProduct("P1", "X", "c", 300)
        assert p.line_price(1) == Decimal("300.00")

    def test_digital_check_qty_max_one(self):
        p = DigitalProduct("P1", "X", "c", 300)
        assert p.check_qty(1) == 1
        with pytest.raises(InvalidQuantityError):
            p.check_qty(2)

    def test_digital_restock_forbidden(self):
        p = DigitalProduct("P1", "X", "c", 300)
        with pytest.raises(InvalidQuantityError):
            p.restock(1)
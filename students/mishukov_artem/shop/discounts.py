from abc import ABC, abstractmethod
from decimal import Decimal

from .exceptions import InvalidPromoError
from .products import to_money


class Discount(ABC):
    """Абстрактный промокод."""

    def __init__(self, code: str):
        self.code = code

    @abstractmethod
    def apply(self, cart) -> Decimal:
        """Сумма скидки в рублях."""

    def validate(self, cart) -> None:
        """Проверить условие применения. Бросает InvalidPromoError."""

    @abstractmethod
    def describe(self) -> str:
        ...


class PercentDiscount(Discount):
    def __init__(self, code: str, percent):
        super().__init__(code)
        self.percent = Decimal(str(percent))

    def apply(self, cart) -> Decimal:
        return to_money(cart.subtotal() * self.percent / Decimal("100"))

    def describe(self):
        return f"{self.code}: −{self.percent}% от суммы"


class FixedDiscount(Discount):
    def __init__(self, code: str, amount, min_total):
        super().__init__(code)
        self.amount = Decimal(str(amount))
        self.min_total = Decimal(str(min_total))

    def validate(self, cart):
        if cart.subtotal() < self.min_total:
            raise InvalidPromoError(
                f"Промокод {self.code} требует сумму не меньше {self.min_total:.2f} ₽"
            )

    def apply(self, cart) -> Decimal:
        st = cart.subtotal()
        if st < self.min_total:
            return Decimal("0")
        return min(self.amount, st)

    def describe(self):
        return f"{self.code}: −{self.amount:.2f} ₽ при сумме ≥ {self.min_total:.2f} ₽"


class ThreeForTwoDiscount(Discount):
    """Каждый третий штучный товар из категории — бесплатно (самые дешёвые)."""

    def __init__(self, code: str, category: str):
        super().__init__(code)
        self.category = category

    def _pieces_in_category(self, cart):
        result = []
        for item in cart.items:
            p = cart.product(item.product_id)
            if p.category == self.category and p.product_type == "piece":
                result.append((p, int(item.qty)))
        return result

    def validate(self, cart):
        total = sum(q for _, q in self._pieces_in_category(cart))
        if total < 3:
            raise InvalidPromoError(
                f"Промокод {self.code} требует минимум 3 шт. в категории «{self.category}»"
            )

    def apply(self, cart) -> Decimal:
        prices = []
        for p, q in self._pieces_in_category(cart):
            prices.extend([p.price] * q)
        prices.sort()
        n = len(prices) // 3
        return to_money(sum(prices[:n], Decimal("0")))

    def describe(self):
        return f"{self.code}: 3 по цене 2 в категории «{self.category}»"


class CategoryPercentDiscount(Discount):
    def __init__(self, code: str, category: str, percent):
        super().__init__(code)
        self.category = category
        self.percent = Decimal(str(percent))

    def apply(self, cart) -> Decimal:
        total = Decimal("0")
        for item in cart.items:
            p = cart.product(item.product_id)
            if p.category == self.category:
                total += p.line_price(item.qty)
        return to_money(total * self.percent / Decimal("100"))

    def describe(self):
        return f"{self.code}: −{self.percent}% на категорию «{self.category}»"


DISCOUNT_TYPES = {
    "percent": PercentDiscount,
    "fixed": FixedDiscount,
    "three_for_two": ThreeForTwoDiscount,
    "category_percent": CategoryPercentDiscount,
}


def create_discount(data: dict) -> Discount:
    t = data.get("type")
    cls = DISCOUNT_TYPES.get(t)
    if cls is None:
        raise ValueError(f"Неизвестный тип промокода: {t!r}")
    code = data["code"]
    if t == "percent":
        return PercentDiscount(code, data["percent"])
    if t == "fixed":
        return FixedDiscount(code, data["amount"], data["min_total"])
    if t == "three_for_two":
        return ThreeForTwoDiscount(code, data["category"])
    if t == "category_percent":
        return CategoryPercentDiscount(code, data["category"], data["percent"])
    raise ValueError(f"Неизвестный тип промокода: {t!r}")
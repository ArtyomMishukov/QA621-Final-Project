from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP

from .exceptions import OutOfStockError, InvalidQuantityError


def to_money(value) -> Decimal:
    """Округление денег до копеек (банковское — ROUND_HALF_UP по требованию)."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def to_dec(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as e:
        raise InvalidQuantityError(f"Некорректное числовое значение: {value!r}") from e


class Product(ABC):
    """Абстрактный товар. Создать напрямую нельзя."""

    product_type: str = ""

    def __init__(self, id: str, name: str, category: str, price):
        self.id = id
        self.name = name
        self.category = category
        self.price = price  # через сеттер с валидацией

    # --- инкапсуляция цены ---
    @property
    def price(self) -> Decimal:
        return self._price

    @price.setter
    def price(self, value):
        v = to_dec(value)
        if v <= 0:
            raise ValueError("Цена должна быть больше нуля")
        self._price = v

    # --- абстрактные операции ---
    @abstractmethod
    def check_qty(self, qty):
        """Проверить и вернуть нормализованное количество."""

    @abstractmethod
    def line_price(self, qty) -> Decimal:
        """Стоимость строки."""

    @abstractmethod
    def deduct(self, qty) -> None:
        """Списать со склада."""

    @abstractmethod
    def restock(self, qty) -> None:
        """Пополнить склад."""

    @abstractmethod
    def type_label(self) -> str:
        ...

    @abstractmethod
    def unit_label(self) -> str:
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        ...

    def __str__(self):
        return f"{self.id} | {self.name} | {self.category} | {self.price} ₽"


class PieceProduct(Product):
    product_type = "piece"

    def __init__(self, id, name, category, price, stock):
        super().__init__(id, name, category, price)
        self.stock = stock

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, value):
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise ValueError("Остаток должен быть целым числом")
        if v < 0:
            raise ValueError("Остаток не может быть отрицательным")
        self._stock = v

    def check_qty(self, qty) -> int:
        d = to_dec(qty)
        if d != d.to_integral_value():
            raise InvalidQuantityError("Для штучного товара количество должно быть целым")
        iq = int(d)
        if iq <= 0:
            raise InvalidQuantityError("Количество должно быть больше нуля")
        if iq > self._stock:
            raise OutOfStockError(
                f"Недостаточно товара «{self.name}»: на складе {self._stock}, запрошено {iq}"
            )
        return iq

    def line_price(self, qty) -> Decimal:
        return to_money(self._price * to_dec(qty))

    def deduct(self, qty):
        iq = self.check_qty(qty)
        self.stock = self._stock - iq

    def restock(self, qty):
        iq = self.check_qty_positive_int(qty)
        self.stock = self._stock + iq

    def check_qty_positive_int(self, qty) -> int:
        d = to_dec(qty)
        if d != d.to_integral_value() or d <= 0:
            raise InvalidQuantityError("Количество для прихода — целое положительное")
        return int(d)

    def type_label(self):
        return "Штучный"

    def unit_label(self):
        return "шт."

    def to_dict(self):
        return {
            "id": self.id,
            "type": "piece",
            "name": self.name,
            "category": self.category,
            "price": float(self._price),
            "stock": self._stock,
        }


class WeightProduct(Product):
    product_type = "weight"

    def __init__(self, id, name, category, price_per_kg, min_kg, stock_kg):
        super().__init__(id, name, category, price_per_kg)
        self.min_kg = to_dec(min_kg)
        self.stock_kg = stock_kg

    @property
    def stock_kg(self) -> Decimal:
        return self._stock_kg

    @stock_kg.setter
    def stock_kg(self, value):
        v = to_dec(value)
        if v < 0:
            raise ValueError("Остаток не может быть отрицательным")
        self._stock_kg = v

    def check_qty(self, qty) -> Decimal:
        q = to_dec(qty)
        if q <= 0:
            raise InvalidQuantityError("Вес должен быть больше нуля")
        if q < self.min_kg:
            raise InvalidQuantityError(
                f"Минимальный вес для «{self.name}» — {self.min_kg} кг"
            )
        if q > self._stock_kg:
            raise OutOfStockError(
                f"Недостаточно товара «{self.name}»: на складе {self._stock_kg} кг, "
                f"запрошено {q} кг"
            )
        return q

    def line_price(self, qty) -> Decimal:
        return to_money(self._price * to_dec(qty))

    def deduct(self, qty):
        q = self.check_qty(qty)
        self.stock_kg = self._stock_kg - q

    def restock(self, qty):
        q = to_dec(qty)
        if q <= 0:
            raise InvalidQuantityError("Вес прихода должен быть больше нуля")
        self.stock_kg = self._stock_kg + q

    def type_label(self):
        return "Весовой"

    def unit_label(self):
        return "кг"

    def to_dict(self):
        return {
            "id": self.id,
            "type": "weight",
            "name": self.name,
            "category": self.category,
            "price_per_kg": float(self._price),
            "min_kg": float(self.min_kg),
            "stock_kg": float(self._stock_kg),
        }


class DigitalProduct(Product):
    product_type = "digital"

    def __init__(self, id, name, category, price):
        super().__init__(id, name, category, price)

    def check_qty(self, qty) -> int:
        d = to_dec(qty)
        if d != d.to_integral_value():
            raise InvalidQuantityError("Цифровой товар — только целое количество")
        iq = int(d)
        if iq <= 0:
            raise InvalidQuantityError("Количество должно быть больше нуля")
        if iq > 1:
            raise InvalidQuantityError("Цифровой товар можно положить в корзину только 1 шт.")
        return iq

    def line_price(self, qty) -> Decimal:
        return to_money(self._price * to_dec(qty))

    def deduct(self, qty):
        self.check_qty(qty)  # просто валидация

    def restock(self, qty):
        raise InvalidQuantityError("Нельзя пополнить цифровой товар")

    def type_label(self):
        return "Цифровой"

    def unit_label(self):
        return "шт."

    def to_dict(self):
        return {
            "id": self.id,
            "type": "digital",
            "name": self.name,
            "category": self.category,
            "price": float(self._price),
        }


PRODUCT_TYPES = {
    "piece": PieceProduct,
    "weight": WeightProduct,
    "digital": DigitalProduct,
}


def create_product(data: dict) -> Product:
    t = data.get("type")
    if t not in PRODUCT_TYPES:
        raise ValueError(f"Неизвестный тип товара: {t!r}")
    if t == "piece":
        return PieceProduct(data["id"], data["name"], data["category"], data["price"], data["stock"])
    if t == "weight":
        return WeightProduct(
            data["id"], data["name"], data["category"],
            data["price_per_kg"], data["min_kg"], data["stock_kg"],
        )
    return DigitalProduct(data["id"], data["name"], data["category"], data["price"])


class Catalog:
    """Каталог товаров: раздаёт товары по id и умеет искать."""

    def __init__(self, products: dict[str, Product]):
        self._products = products

    def get(self, product_id: str) -> Product:
        p = self._products.get(product_id)
        if p is None:
            from .exceptions import ProductNotFoundError
            raise ProductNotFoundError(f"Товар с артикулом {product_id} не найден")
        return p

    def all(self) -> list[Product]:
        return list(self._products.values())

    def filter_by_category(self, category: str) -> list[Product]:
        return [p for p in self._products.values() if p.category == category]

    def search(self, query: str) -> list[Product]:
        q = query.lower()
        return [p for p in self._products.values() if q in p.name.lower()]
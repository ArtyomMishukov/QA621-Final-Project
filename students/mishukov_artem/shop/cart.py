from dataclasses import dataclass
from decimal import Decimal

from .exceptions import EmptyCartError, ProductNotFoundError
from .products import to_money


@dataclass
class CartItem:
    product_id: str
    qty: object  # int для piece/digital, Decimal для weight

    def to_dict(self):
        q = float(self.qty) if isinstance(self.qty, Decimal) else int(self.qty)
        return {"product_id": self.product_id, "qty": q}


class Cart:
    """Корзина. Хранит ссылку на каталог для резолва товаров."""

    def __init__(self, catalog):
        self._catalog = catalog
        self.items: list[CartItem] = []
        self.promo = None
        self.promo_code: str | None = None

    # --- dunder-магия ---
    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __contains__(self, product_id):
        return any(it.product_id == product_id for it in self.items)

    def __bool__(self):
        return bool(self.items)

    # --- операции ---
    def product(self, product_id):
        return self._catalog.get(product_id)

    def add(self, product_id, qty):
        product = self._catalog.get(product_id)
        norm = product.check_qty(qty)
        for item in self.items:
            if item.product_id == product_id:
                item.qty = product.check_qty(item.qty + norm)
                return item
        item = CartItem(product_id, norm)
        self.items.append(item)
        return item

    def set_qty(self, product_id, qty):
        product = self._catalog.get(product_id)
        norm = product.check_qty(qty)
        for item in self.items:
            if item.product_id == product_id:
                item.qty = norm
                return item
        raise ProductNotFoundError(f"Товар {product_id} отсутствует в корзине")

    def remove(self, product_id):
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                del self.items[i]
                return
        raise ProductNotFoundError(f"Товар {product_id} отсутствует в корзине")

    def clear(self):
        self.items.clear()
        self.promo = None
        self.promo_code = None

    # --- суммы ---
    def subtotal(self) -> Decimal:
        total = Decimal("0")
        for item in self.items:
            p = self._catalog.get(item.product_id)
            total += p.line_price(item.qty)
        return to_money(total)

    def discount_amount(self) -> Decimal:
        if not self.promo:
            return Decimal("0")
        return to_money(self.promo.apply(self))

    def total(self) -> Decimal:
        t = self.subtotal() - self.discount_amount()
        return to_money(max(Decimal("0"), t))

    def require_non_empty(self):
        if not self.items:
            raise EmptyCartError("Корзина пуста")
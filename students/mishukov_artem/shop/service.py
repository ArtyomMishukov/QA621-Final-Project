import csv
from decimal import Decimal
from pathlib import Path

from .cart import Cart, CartItem
from .decorators import log_action
from .discounts import create_discount
from .exceptions import (
    EmptyCartError,
    InvalidOrderError,
    InvalidPromoError,
    OutOfStockError,
    ProductNotFoundError,
    ShopError,
)
from .orders import Order
from .products import Catalog, create_product


class ShopService:
    """Бизнес-логика магазина."""

    def __init__(self, repo, log_path=None):
        self.repo = repo
        self.log_path = log_path or (repo.data_dir / "shop.log")
        self._orders_data = repo.load_orders()
        self.catalog = self._load_catalog()
        self.promos = self._load_promos()
        self.cart = self._build_cart()

    # --- загрузка ---
    def _load_catalog(self) -> Catalog:
        data = self.repo.load_catalog()
        products = {}
        for raw in data.get("products", []):
            p = create_product(raw)
            products[p.id] = p
        return Catalog(products)

    def _load_promos(self) -> dict:
        data = self.repo.load_promos()
        promos = {}
        for raw in data.get("promos", []):
            d = create_discount(raw)
            promos[d.code] = d
        return promos

    def _build_cart(self) -> Cart:
        cart = Cart(self.catalog)
        cart_data = self._orders_data.get("cart", {})
        for raw in cart_data.get("items", []):
            try:
                product = self.catalog.get(raw["product_id"])
            except ProductNotFoundError:
                continue
            if product.product_type == "piece":
                qty = int(raw["qty"])
            elif product.product_type == "digital":
                qty = int(raw["qty"])
            else:
                qty = Decimal(str(raw["qty"]))
            cart.items.append(CartItem(raw["product_id"], qty))
        code = cart_data.get("promo")
        if code:
            cart.promo_code = code
            cart.promo = self.promos.get(code)
        return cart

    # --- сохранение ---
    def _save_orders(self) -> None:
        self._orders_data["cart"] = {
            "items": [it.to_dict() for it in self.cart.items],
            "promo": self.cart.promo_code,
        }
        self.repo.save_orders(self._orders_data)

    def _save_catalog(self) -> None:
        self.repo.save_catalog(
            {"products": [p.to_dict() for p in self.catalog.all()]}
        )

    # --- корзина ---
    @log_action
    def add_to_cart(self, product_id, qty):
        self.cart.add(product_id, qty)
        self._save_orders()

    @log_action
    def set_cart_qty(self, product_id, qty):
        self.cart.set_qty(product_id, qty)
        self._save_orders()

    @log_action
    def remove_from_cart(self, product_id):
        self.cart.remove(product_id)
        self._save_orders()

    # --- промокод ---
    @log_action
    def apply_promo(self, code):
        promo = self.promos.get(code)
        if promo is None:
            raise InvalidPromoError(f"Неизвестный промокод: {code}")
        promo.validate(self.cart)
        self.cart.promo = promo
        self.cart.promo_code = code
        self._save_orders()

    # --- оформление ---
    @log_action
    def checkout(self) -> Order:
        self.cart.require_non_empty()

        # 1. Проверяем остатки по всем позициям
        for item in self.cart.items:
            product = self.catalog.get(item.product_id)
            product.check_qty(item.qty)

        # 2. Считаем суммы
        subtotal = self.cart.subtotal()
        discount = self.cart.discount_amount()
        total = self.cart.total()

        # 3. Формируем позиции заказа (с текущей ценой)
        order_items = []
        for item in self.cart.items:
            product = self.catalog.get(item.product_id)
            order_items.append(
                {
                    "product_id": item.product_id,
                    "qty": float(item.qty) if isinstance(item.qty, Decimal) else int(item.qty),
                    "price": float(product.price),
                    "line_total": float(product.line_price(item.qty)),
                }
            )

        # 4. Списываем остатки
        for item in self.cart.items:
            product = self.catalog.get(item.product_id)
            product.deduct(item.qty)

        # 5. Создаём заказ
        order_id = self._orders_data["next_order_id"]
        order = Order(
            id=order_id,
            items=order_items,
            subtotal=float(subtotal),
            discount=float(discount),
            total=float(total),
            promo=self.cart.promo_code,
            status="new",
        )
        self._orders_data["orders"].append(order.to_dict())
        self._orders_data["next_order_id"] = order_id + 1

        # 6. Очищаем корзину и сохраняем
        self.cart.clear()
        self._save_orders()
        self._save_catalog()
        return order

    # --- отмена ---
    @log_action
    def cancel_order(self, order_id: int) -> None:
        raw = self.find_order_raw(order_id)
        if raw["status"] == "cancelled":
            raise InvalidOrderError(f"Заказ #{order_id} уже отменён")
        # Возвращаем остатки
        for it in raw["items"]:
            try:
                product = self.catalog.get(it["product_id"])
            except ProductNotFoundError:
                continue
            try:
                product.restock(it["qty"])
            except ShopError:
                continue
        raw["status"] = "cancelled"
        self._save_orders()
        self._save_catalog()

    # --- склад ---
    @log_action
    def restock(self, product_id, qty) -> None:
        product = self.catalog.get(product_id)
        product.restock(qty)
        self._save_catalog()

    # --- чтение ---
    def list_orders(self) -> list[Order]:
        return [Order.from_dict(o) for o in self._orders_data.get("orders", [])]

    def find_order_raw(self, order_id: int) -> dict:
        for o in self._orders_data.get("orders", []):
            if o.get("id") == order_id:
                return o
        raise InvalidOrderError(f"Заказ #{order_id} не найден")

    def get_order(self, order_id: int) -> Order:
        return Order.from_dict(self.find_order_raw(order_id))

    # --- экспорт ---
    @log_action
    def export_orders(self, path) -> int:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        orders = self._orders_data.get("orders", [])
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                ["id", "status", "items_count", "subtotal", "discount", "total"]
            )
            for o in orders:
                writer.writerow(
                    [
                        o["id"],
                        o["status"],
                        len(o.get("items", [])),
                        f"{o.get('subtotal', 0):.2f}",
                        f"{o.get('discount', 0):.2f}",
                        f"{o.get('total', 0):.2f}",
                    ]
                )
        return len(orders)
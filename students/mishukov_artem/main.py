import sys
from argparse import ArgumentParser
from pathlib import Path

from shop.exceptions import ShopError
from shop.repository import Repository
from shop.service import ShopService

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

def build_parser():
    p = ArgumentParser(prog="shop", description="Магазин настольных игр")
    sub = p.add_subparsers(dest="command", required=True)

    cat = sub.add_parser("catalog", help="Каталог товаров")
    cat.add_argument("--category", default=None, help="Фильтр по категории")

    search = sub.add_parser("search", help="Поиск по названию")
    search.add_argument("query")

    show = sub.add_parser("show", help="Карточка товара")
    show.add_argument("product_id")

    cart = sub.add_parser("cart", help="Корзина")
    cart_sub = cart.add_subparsers(dest="cart_action", required=True)
    ca = cart_sub.add_parser("add"); ca.add_argument("product_id"); ca.add_argument("qty")
    cs = cart_sub.add_parser("set"); cs.add_argument("product_id"); cs.add_argument("qty")
    cr = cart_sub.add_parser("remove"); cr.add_argument("product_id")
    cart_sub.add_parser("show")

    promo = sub.add_parser("promo", help="Применить промокод")
    promo.add_argument("code")

    sub.add_parser("checkout", help="Оформить заказ")
    sub.add_parser("orders", help="Список заказов")

    order = sub.add_parser("order", help="Информация о заказе")
    order.add_argument("order_id", type=int)

    cancel = sub.add_parser("cancel", help="Отменить заказ")
    cancel.add_argument("order_id", type=int)

    rs = sub.add_parser("restock", help="Пополнить склад")
    rs.add_argument("product_id")
    rs.add_argument("qty")

    exp = sub.add_parser("export-orders", help="Экспорт в CSV")
    exp.add_argument("path")

    return p


# --- вывод ---
def _stock_label(p):
    if p.product_type == "digital":
        return "∞"
    if p.product_type == "weight":
        return f"{float(p.stock_kg)} кг"
    return str(p.stock)


def _qty_fmt(q):
    if isinstance(q, float) or hasattr(q, "quantize"):
        f = float(q)
        return str(int(f)) if f == int(f) else str(f)
    return str(q)


def print_catalog(products):
    if not products:
        print("Ничего не найдено")
        return
    print(f"{'ID':<6} {'Название':<32} {'Категория':<14} {'Цена, ₽':>10} {'Остаток':>12}")
    for p in products:
        print(
            f"{p.id:<6} {p.name[:32]:<32} {p.category:<14} "
            f"{float(p.price):>10.2f} {_stock_label(p):>12}"
        )


def print_product(p):
    print(f"Артикул:   {p.id}")
    print(f"Название:  {p.name}")
    print(f"Категория: {p.category}")
    print(f"Тип:       {p.type_label()}")
    print(f"Цена:      {float(p.price):.2f} ₽ / {p.unit_label()}")
    if p.product_type == "weight":
        print(f"Мин. вес:  {float(p.min_kg)} кг")
        print(f"Остаток:   {float(p.stock_kg)} кг")
    elif p.product_type == "digital":
        print("Склад:     не требуется")
        print("В корзину: максимум 1 шт.")
    else:
        print(f"Остаток:   {p.stock} шт.")


def print_cart(service):
    if not service.cart:
        print("Корзина пуста")
        return
    print(f"{'ID':<6} {'Название':<28} {'Кол-во':>8} {'Цена':>10} {'Сумма':>10}")
    for it in service.cart:
        p = service.catalog.get(it.product_id)
        print(
            f"{p.id:<6} {p.name[:28]:<28} {_qty_fmt(it.qty):>8} "
            f"{float(p.price):>10.2f} {float(p.line_price(it.qty)):>10.2f}"
        )
    print()
    print(f"Сумма без скидки: {float(service.cart.subtotal()):.2f} ₽")
    print(f"Скидка:           {float(service.cart.discount_amount()):.2f} ₽")
    print(f"Итого:            {float(service.cart.total()):.2f} ₽")
    if service.cart.promo:
        print(f"Промокод:         {service.cart.promo.code}")


def print_order(o):
    print(f"Заказ #{o.id}   статус: {o.status}")
    if o.promo:
        print(f"Промокод: {o.promo}")
    print(f"{'ID':<6} {'Кол-во':>8} {'Цена':>10} {'Сумма':>10}")
    for it in o.items:
        print(
            f"{it['product_id']:<6} {_qty_fmt(it['qty']):>8} "
            f"{it['price']:>10.2f} {it['line_total']:>10.2f}"
        )
    print()
    print(f"Сумма без скидки: {o.subtotal:.2f} ₽")
    print(f"Скидка:           {o.discount:.2f} ₽")
    print(f"Итого:            {o.total:.2f} ₽")


def main():
    parser = build_parser()
    args = parser.parse_args()

    data_dir = Path(__file__).parent / "data"
    repo = Repository(data_dir)

    try:
        service = ShopService(repo, log_path=data_dir / "shop.log")
    except ShopError as e:
        print(f"Ошибка загрузки данных: {e}")
        return 1

    try:
        if args.command == "catalog":
            prods = service.catalog.all()
            if args.category:
                prods = [p for p in prods if p.category == args.category]
            print_catalog(prods)

        elif args.command == "search":
            print_catalog(service.catalog.search(args.query))

        elif args.command == "show":
            print_product(service.catalog.get(args.product_id))

        elif args.command == "cart":
            if args.cart_action == "add":
                service.add_to_cart(args.product_id, args.qty)
                print(f"Добавлено: {args.product_id} × {args.qty}")
            elif args.cart_action == "set":
                service.set_cart_qty(args.product_id, args.qty)
                print(f"Количество {args.product_id} = {args.qty}")
            elif args.cart_action == "remove":
                service.remove_from_cart(args.product_id)
                print(f"Удалено: {args.product_id}")
            elif args.cart_action == "show":
                print_cart(service)

        elif args.command == "promo":
            service.apply_promo(args.code)
            print(f"Промокод {args.code} применён")

        elif args.command == "checkout":
            order = service.checkout()
            print(f"Заказ #{order.id} оформлен на {order.total:.2f} ₽")

        elif args.command == "orders":
            orders = service.list_orders()
            if not orders:
                print("Заказов пока нет")
            for o in orders:
                print(o)

        elif args.command == "order":
            print_order(service.get_order(args.order_id))

        elif args.command == "cancel":
            service.cancel_order(args.order_id)
            print(f"Заказ #{args.order_id} отменён, остатки возвращены")

        elif args.command == "restock":
            service.restock(args.product_id, args.qty)
            print(f"Склад пополнен: {args.product_id} +{args.qty}")

        elif args.command == "export-orders":
            n = service.export_orders(args.path)
            print(f"Экспортировано {n} заказов в {args.path}")

    except ShopError as e:
        print(f"Ошибка: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
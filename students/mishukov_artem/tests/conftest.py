import json
import pytest

from shop.cart import Cart
from shop.products import Catalog, create_product
from shop.repository import Repository
from shop.service import ShopService


CATALOG = {
    "products": [
        {"id": "P001", "type": "piece", "name": "Игра А",
         "category": "boardgames", "price": 1000, "stock": 3},
        {"id": "P002", "type": "piece", "name": "Игра Б",
         "category": "boardgames", "price": 500, "stock": 5},
        {"id": "P004", "type": "piece", "name": "Пазл",
         "category": "puzzles", "price": 400, "stock": 10},
        {"id": "P010", "type": "weight", "name": "Кубики",
         "category": "dice", "price_per_kg": 2400, "min_kg": 0.1, "stock_kg": 2.0},
        {"id": "P020", "type": "digital", "name": "PDF",
         "category": "digital", "price": 300},
    ]
}

PROMOS = {
    "promos": [
        {"code": "SALE10",    "type": "percent",          "percent": 10},
        {"code": "MINUS500",  "type": "fixed",            "amount": 500, "min_total": 3000},
        {"code": "BOARD3",    "type": "three_for_two",    "category": "boardgames"},
        {"code": "PUZZLE15",  "type": "category_percent", "category": "puzzles", "percent": 15},
    ]
}


# --- фикстура 1: сырые данные каталога (копия, чтобы тесты не портили друг друга) ---
@pytest.fixture
def catalog_data():
    return json.loads(json.dumps(CATALOG))


# --- фикстура 2: сырые данные промокодов ---
@pytest.fixture
def promos_data():
    return json.loads(json.dumps(PROMOS))


# --- фикстура 3: объект Catalog с товарами ---
@pytest.fixture
def catalog(catalog_data):
    products = {p["id"]: create_product(p) for p in catalog_data["products"]}
    return Catalog(products)


# --- фикстура 4: пустая корзина поверх каталога ---
@pytest.fixture
def cart(catalog):
    return Cart(catalog)


# --- фикстура 5: Repository поверх tmp_path с готовыми catalog.json и promos.json ---
@pytest.fixture
def repo(tmp_path, catalog_data, promos_data):
    data = tmp_path / "data"
    data.mkdir()
    (data / "catalog.json").write_text(
        json.dumps(catalog_data, ensure_ascii=False), encoding="utf-8"
    )
    (data / "promos.json").write_text(
        json.dumps(promos_data, ensure_ascii=False), encoding="utf-8"
    )
    return Repository(data)


# --- фикстура 6 (yield): сервис с чистым логом ---
@pytest.fixture
def service(repo, tmp_path):
    svc = ShopService(repo, log_path=tmp_path / "shop.log")
    yield svc
    # cleanup после теста — демонстрирует yield-фикстуру
    log = tmp_path / "shop.log"
    if log.exists():
        log.unlink()
import pytest

from shop.exceptions import DataFileError
from shop.repository import Repository


def test_repository_save_and_load_match(tmp_path):
    repo = Repository(tmp_path)
    data = {
        "cart": {"items": [{"product_id": "P001", "qty": 1}], "promo": "SALE10"},
        "orders": [{"id": 1, "status": "new", "items": []}],
        "next_order_id": 2,
    }
    repo.save_orders(data)
    assert repo.load_orders() == data


def test_repository_missing_catalog_raises(tmp_path):
    repo = Repository(tmp_path)
    with pytest.raises(DataFileError):
        repo.load_catalog()


def test_repository_missing_promos_raises(tmp_path):
    repo = Repository(tmp_path)
    with pytest.raises(DataFileError):
        repo.load_promos()


def test_repository_broken_json_raises(tmp_path):
    (tmp_path / "catalog.json").write_text("{not valid json", encoding="utf-8")
    repo = Repository(tmp_path)
    with pytest.raises(DataFileError):
        repo.load_catalog()


def test_repository_missing_orders_returns_default(tmp_path):
    repo = Repository(tmp_path)
    default = repo.load_orders()
    assert default["orders"] == []
    assert default["next_order_id"] == 1
    assert default["cart"] == {"items": [], "promo": None}


def test_repository_reads_file_with_utf8_bom(tmp_path):
    # Windows PowerShell пишет BOM — Repository должен это пережить
    path = tmp_path / "catalog.json"
    path.write_bytes(
        b"\xef\xbb\xbf" + '{"products": []}'.encode("utf-8")
    )
    repo = Repository(tmp_path)
    assert repo.load_catalog() == {"products": []}
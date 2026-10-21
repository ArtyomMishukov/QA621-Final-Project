import json
from pathlib import Path

from .exceptions import DataFileError


class Repository:
    """Работа с JSON-файлами. Путь к data/ передаётся явно (для тестов)."""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.catalog_path = self.data_dir / "catalog.json"
        self.promos_path = self.data_dir / "promos.json"
        self.orders_path = self.data_dir / "orders.json"

    def _read(self, path: Path, default=None):
        if not path.exists():
            if default is not None:
                return default
            raise DataFileError(f"Файл не найден: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DataFileError(f"Битый JSON в {path}: {e}") from e
        except OSError as e:
            raise DataFileError(f"Ошибка чтения {path}: {e}") from e

    def _write(self, path: Path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(path)

    # --- catalog ---
    def load_catalog(self) -> dict:
        return self._read(self.catalog_path)

    def save_catalog(self, data: dict) -> None:
        self._write(self.catalog_path, data)

    # --- promos ---
    def load_promos(self) -> dict:
        return self._read(self.promos_path)

    # --- orders ---
    def load_orders(self) -> dict:
        default = {
            "cart": {"items": [], "promo": None},
            "orders": [],
            "next_order_id": 1,
        }
        return self._read(self.orders_path, default=default)

    def save_orders(self, data: dict) -> None:
        self._write(self.orders_path, data)
# Магазин настольных игр

Консольное приложение с полноценным ООП, файловым хранилищем (JSON) и тестами на pytest.

## Требования

- Python 3.10+
- `pytest` (см. `requirements.txt`)

Установка зависимостей:

```bash
pip install -r requirements.txt

## Запуск
python main.py catalog
python main.py cart add P001 2
python main.py checkout

## Команды
(перечисли все: catalog, search, show, cart add/set/remove/show,
promo, checkout, orders, order, cancel, restock, export-orders)

## Типы товаров и промокодов
piece / weight / digital; SALE10 / MINUS500 / BOARD3 / PUZZLE15

## Тесты
pytest -v
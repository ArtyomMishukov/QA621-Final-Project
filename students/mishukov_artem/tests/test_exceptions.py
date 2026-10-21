from shop import exceptions as exc


def test_all_custom_exceptions_inherit_shop_error():
    for cls in [
        exc.ProductNotFoundError,
        exc.OutOfStockError,
        exc.InvalidQuantityError,
        exc.InvalidPromoError,
        exc.EmptyCartError,
        exc.DataFileError,
        exc.InvalidOrderError,
    ]:
        assert issubclass(cls, exc.ShopError)
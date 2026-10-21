class ShopError(Exception):
    """Базовое исключение приложения."""


class ProductNotFoundError(ShopError):
    pass


class OutOfStockError(ShopError):
    pass


class InvalidQuantityError(ShopError):
    pass


class InvalidPromoError(ShopError):
    pass


class EmptyCartError(ShopError):
    pass


class DataFileError(ShopError):
    pass


class InvalidOrderError(ShopError):
    pass
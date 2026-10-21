from dataclasses import dataclass, asdict


@dataclass
class Order:
    id: int
    items: list
    subtotal: float
    discount: float
    total: float
    promo: str | None
    status: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Order":
        return cls(
            id=d["id"],
            items=d.get("items", []),
            subtotal=d.get("subtotal", 0.0),
            discount=d.get("discount", 0.0),
            total=d.get("total", 0.0),
            promo=d.get("promo"),
            status=d.get("status", "new"),
        )

    def __str__(self):
        return (
            f"Заказ #{self.id} [{self.status}] — {self.total:.2f} ₽ "
            f"(скидка {self.discount:.2f})"
        )
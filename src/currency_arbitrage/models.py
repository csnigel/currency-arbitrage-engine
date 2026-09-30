from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import count


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Fill:
    quantity: float
    price: float


_ORDER_IDS = count(1)


@dataclass
class Order:
    base: str
    quote: str
    side: Side
    price: float
    quantity: float
    timestamp: int
    order_id: int = field(default_factory=lambda: next(_ORDER_IDS))
    remaining: float = field(init=False)
    fills: list[Fill] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.base = self.base.upper()
        self.quote = self.quote.upper()
        self.side = Side(self.side)
        if self.base == self.quote:
            raise ValueError("base and quote currencies must differ")
        if self.price <= 0 or self.quantity <= 0:
            raise ValueError("price and quantity must be positive")
        self.remaining = float(self.quantity)

    @property
    def filled_quantity(self) -> float:
        return sum(fill.quantity for fill in self.fills)

    @property
    def is_filled(self) -> bool:
        return self.remaining <= 1e-12

    @property
    def average_fill_price(self) -> float | None:
        quantity = self.filled_quantity
        if quantity <= 0:
            return None
        return sum(fill.quantity * fill.price for fill in self.fills) / quantity

from __future__ import annotations

from collections.abc import Iterable

from .models import Order
from .order_book import OrderBook


class Exchange:
    def __init__(self, currency_pairs: Iterable[tuple[str, str]]):
        self.order_books: dict[tuple[str, str], OrderBook] = {}
        for base, quote in currency_pairs:
            pair = (base.upper(), quote.upper())
            if pair in self.order_books:
                raise ValueError(f"duplicate currency pair: {pair}")
            self.order_books[pair] = OrderBook(*pair)

    def submit(self, order: Order) -> Order:
        pair = (order.base, order.quote)
        if pair not in self.order_books:
            raise KeyError(f"unsupported currency pair: {pair}")
        return self.order_books[pair].process(order)

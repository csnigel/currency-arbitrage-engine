from __future__ import annotations

import heapq
from itertools import count

from .models import Fill, Order, Side


class _OrderQueue:
    def __init__(self, side: Side):
        self.side = side
        self._sequence = count()
        self._heap: list[tuple[float, int, int, Order]] = []

    def _price_key(self, order: Order) -> float:
        return -order.price if self.side is Side.BUY else order.price

    def push(self, order: Order) -> None:
        heapq.heappush(
            self._heap,
            (self._price_key(order), order.timestamp, next(self._sequence), order),
        )

    def _discard_filled(self) -> None:
        while self._heap and self._heap[0][3].is_filled:
            heapq.heappop(self._heap)

    def peek(self) -> Order | None:
        self._discard_filled()
        return self._heap[0][3] if self._heap else None

    def pop(self) -> Order | None:
        self._discard_filled()
        return heapq.heappop(self._heap)[3] if self._heap else None

    def __len__(self) -> int:
        self._discard_filled()
        return len(self._heap)


class OrderBook:
    """One base/quote limit order book with price-time priority."""

    def __init__(self, base: str, quote: str):
        self.base = base.upper()
        self.quote = quote.upper()
        self.bids = _OrderQueue(Side.BUY)
        self.asks = _OrderQueue(Side.SELL)

    @property
    def best_bid(self) -> Order | None:
        return self.bids.peek()

    @property
    def best_ask(self) -> Order | None:
        return self.asks.peek()

    def process(self, order: Order) -> Order:
        if (order.base, order.quote) != (self.base, self.quote):
            raise ValueError("order currency pair does not match this book")

        opposite = self.asks if order.side is Side.BUY else self.bids
        own = self.bids if order.side is Side.BUY else self.asks

        while order.remaining > 1e-12:
            resting = opposite.peek()
            if resting is None:
                break
            crosses = resting.price <= order.price if order.side is Side.BUY else resting.price >= order.price
            if not crosses:
                break
            quantity = min(order.remaining, resting.remaining)
            price = resting.price
            order.remaining -= quantity
            resting.remaining -= quantity
            order.fills.append(Fill(quantity, price))
            resting.fills.append(Fill(quantity, price))
            # The next peek discards the filled top order. Calling pop here
            # would first discard that fill and then remove the next live
            # order, skipping valid liquidity at the same or next price.

        if order.remaining > 1e-12:
            own.push(order)
        return order

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .exchange import Exchange
from .graph import build_conversion_graph, cycle_return, edge_lookup, find_negative_cycle
from .models import Order, Side
from .order_book import OrderBook


@dataclass(frozen=True)
class ArbitragePlan:
    cycle: tuple[str, ...]
    orders: tuple[Order, ...]
    starting_amount: float
    expected_ending_amount: float

    @property
    def expected_profit(self) -> float:
        return self.expected_ending_amount - self.starting_amount


class ArbitrageBot:
    def __init__(self):
        self.positions: defaultdict[str, float] = defaultdict(float)

    def find_plan(
        self,
        order_books: dict[tuple[str, str], OrderBook],
        timestamp: int,
    ) -> ArbitragePlan | None:
        graph = build_conversion_graph(order_books)
        cycle = find_negative_cycle(graph)
        if cycle is None:
            return None
        lookup = edge_lookup(graph)

        cumulative_rate = 1.0
        starting_capacity = float("inf")
        for source, target in zip(cycle, cycle[1:]):
            edge = lookup[(source, target)]
            starting_capacity = min(starting_capacity, edge.input_capacity / cumulative_rate)
            cumulative_rate *= edge.rate
        if not (starting_capacity > 0 and starting_capacity < float("inf")):
            return None

        orders: list[Order] = []
        input_amount = starting_capacity
        for source, target in zip(cycle, cycle[1:]):
            edge = lookup[(source, target)]
            output_amount = input_amount * edge.rate
            quantity = input_amount if edge.order_side is Side.SELL else output_amount
            orders.append(
                Order(
                    base=edge.pair[0],
                    quote=edge.pair[1],
                    side=edge.order_side,
                    price=edge.limit_price,
                    quantity=quantity,
                    timestamp=timestamp,
                )
            )
            input_amount = output_amount
        expected_end = starting_capacity * cycle_return(cycle, graph)
        return ArbitragePlan(cycle, tuple(orders), starting_capacity, expected_end)

    def execute(self, plan: ArbitragePlan, exchange: Exchange) -> None:
        for order in plan.orders:
            exchange.submit(order)
            for fill in order.fills:
                if order.side is Side.BUY:
                    self.positions[order.base] += fill.quantity
                    self.positions[order.quote] -= fill.quantity * fill.price
                else:
                    self.positions[order.base] -= fill.quantity
                    self.positions[order.quote] += fill.quantity * fill.price

    def rounded_positions(self, digits: int = 6) -> dict[str, float]:
        return {currency: round(value, digits) for currency, value in sorted(self.positions.items())}

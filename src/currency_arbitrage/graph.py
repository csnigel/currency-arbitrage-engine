from __future__ import annotations

from dataclasses import dataclass
import math

from .models import Side
from .order_book import OrderBook


@dataclass(frozen=True)
class ConversionEdge:
    source: str
    target: str
    rate: float
    input_capacity: float
    pair: tuple[str, str]
    order_side: Side
    limit_price: float

    @property
    def log_cost(self) -> float:
        return -math.log(self.rate)


def build_conversion_graph(order_books: dict[tuple[str, str], OrderBook]) -> dict[str, list[ConversionEdge]]:
    graph: dict[str, list[ConversionEdge]] = {}
    for pair, book in order_books.items():
        base, quote = pair
        graph.setdefault(base, [])
        graph.setdefault(quote, [])
        bid = book.best_bid
        if bid is not None:
            graph[base].append(
                ConversionEdge(base, quote, bid.price, bid.remaining, pair, Side.SELL, bid.price)
            )
        ask = book.best_ask
        if ask is not None:
            graph[quote].append(
                ConversionEdge(
                    quote,
                    base,
                    1.0 / ask.price,
                    ask.remaining * ask.price,
                    pair,
                    Side.BUY,
                    ask.price,
                )
            )
    for edges in graph.values():
        edges.sort(key=lambda edge: (edge.target, edge.limit_price, edge.order_side.value))
    return graph


def find_negative_cycle(graph: dict[str, list[ConversionEdge]], tolerance: float = 1e-12) -> tuple[str, ...] | None:
    """Return one directed negative-cost cycle using a virtual super-source."""
    nodes = sorted(graph)
    if not nodes:
        return None
    distance = {node: 0.0 for node in nodes}
    predecessor: dict[str, str] = {}
    updated: str | None = None

    for _ in range(len(nodes)):
        updated = None
        for source in nodes:
            for edge in graph.get(source, []):
                candidate = distance[source] + edge.log_cost
                if candidate < distance[edge.target] - tolerance:
                    distance[edge.target] = candidate
                    predecessor[edge.target] = source
                    updated = edge.target
        if updated is None:
            return None

    cursor = updated
    for _ in nodes:
        if cursor not in predecessor:
            return None
        cursor = predecessor[cursor]

    reverse_cycle = [cursor]
    current = predecessor[cursor]
    while current != cursor:
        if current in reverse_cycle or current not in predecessor:
            return None
        reverse_cycle.append(current)
        current = predecessor[current]
    reverse_cycle.append(cursor)
    cycle = tuple(reversed(reverse_cycle))
    return cycle if cycle_return(cycle, graph) > 1.0 + tolerance else None


def edge_lookup(graph: dict[str, list[ConversionEdge]]) -> dict[tuple[str, str], ConversionEdge]:
    return {(edge.source, edge.target): edge for edges in graph.values() for edge in edges}


def cycle_return(cycle: tuple[str, ...], graph: dict[str, list[ConversionEdge]]) -> float:
    if len(cycle) < 2 or cycle[0] != cycle[-1]:
        raise ValueError("cycle must contain at least one edge and return to its start")
    lookup = edge_lookup(graph)
    value = 1.0
    for source, target in zip(cycle, cycle[1:]):
        edge = lookup.get((source, target))
        if edge is None:
            raise ValueError(f"cycle contains unavailable conversion: {source}->{target}")
        value *= edge.rate
    return value

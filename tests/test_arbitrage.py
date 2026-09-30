import pytest

from currency_arbitrage import (
    ArbitrageBot,
    Exchange,
    Order,
    Side,
    build_conversion_graph,
    cycle_return,
    find_negative_cycle,
)


def seeded_exchange() -> Exchange:
    exchange = Exchange([("USD", "EUR"), ("EUR", "GBP"), ("USD", "GBP")])
    exchange.submit(Order("USD", "EUR", Side.BUY, 0.90, 100.0, 0))
    exchange.submit(Order("EUR", "GBP", Side.BUY, 0.90, 100.0, 0))
    exchange.submit(Order("USD", "GBP", Side.SELL, 0.75, 200.0, 0))
    return exchange


def test_detects_profitable_cycle():
    graph = build_conversion_graph(seeded_exchange().order_books)
    cycle = find_negative_cycle(graph)

    assert cycle is not None
    assert cycle_return(cycle, graph) == pytest.approx(1.08)


def test_plan_respects_liquidity_and_reconciles_profit():
    exchange = seeded_exchange()
    bot = ArbitrageBot()
    plan = bot.find_plan(exchange.order_books, timestamp=1)

    assert plan is not None
    assert plan.starting_amount == pytest.approx(83.3333333333)
    assert plan.expected_profit == pytest.approx(6.6666666667)

    bot.execute(plan, exchange)
    positions = bot.rounded_positions()
    assert positions["EUR"] == pytest.approx(6.6666666667)
    assert positions["GBP"] == pytest.approx(0.0)
    assert positions["USD"] == pytest.approx(0.0)


def test_no_cycle_when_quotes_are_consistent():
    exchange = Exchange([("USD", "EUR"), ("EUR", "GBP"), ("USD", "GBP")])
    exchange.submit(Order("USD", "EUR", Side.BUY, 0.90, 100.0, 0))
    exchange.submit(Order("EUR", "GBP", Side.BUY, 0.80, 100.0, 0))
    exchange.submit(Order("USD", "GBP", Side.SELL, 0.73, 200.0, 0))

    graph = build_conversion_graph(exchange.order_books)
    assert find_negative_cycle(graph) is None

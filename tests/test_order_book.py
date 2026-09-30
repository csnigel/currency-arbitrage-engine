import pytest

from currency_arbitrage import Order, OrderBook, Side


def test_price_time_priority_and_partial_fill():
    book = OrderBook("USD", "EUR")
    later = book.process(Order("USD", "EUR", Side.SELL, 0.90, 5.0, 2))
    earlier = book.process(Order("USD", "EUR", Side.SELL, 0.90, 4.0, 1))
    incoming = book.process(Order("USD", "EUR", Side.BUY, 0.91, 6.0, 3))

    assert incoming.is_filled
    assert incoming.average_fill_price == pytest.approx(0.90)
    assert earlier.is_filled
    assert later.remaining == pytest.approx(3.0)


def test_non_crossing_order_rests():
    book = OrderBook("USD", "EUR")
    bid = book.process(Order("USD", "EUR", Side.BUY, 0.89, 10.0, 0))
    ask = book.process(Order("USD", "EUR", Side.SELL, 0.90, 10.0, 1))

    assert bid.filled_quantity == 0
    assert ask.filled_quantity == 0
    assert book.best_bid is bid
    assert book.best_ask is ask


def test_unfilled_order_has_no_average_fill_price():
    order = Order("USD", "EUR", Side.BUY, 0.89, 10.0, 0)

    assert order.average_fill_price is None

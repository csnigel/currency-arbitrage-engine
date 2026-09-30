from currency_arbitrage import ArbitrageBot, Exchange, Order, Side


def main() -> None:
    exchange = Exchange([("USD", "EUR"), ("EUR", "GBP"), ("USD", "GBP")])
    exchange.submit(Order("USD", "EUR", Side.BUY, 0.90, 100.0, 0))
    exchange.submit(Order("EUR", "GBP", Side.BUY, 0.90, 100.0, 0))
    exchange.submit(Order("USD", "GBP", Side.SELL, 0.75, 200.0, 0))

    bot = ArbitrageBot()
    plan = bot.find_plan(exchange.order_books, timestamp=1)
    if plan is None:
        print("No executable arbitrage found.")
        return

    print("Synthetic simulation - not live trading performance")
    print("Cycle:", " -> ".join(plan.cycle))
    print(f"Starting amount: {plan.starting_amount:.4f} {plan.cycle[0]}")
    print(f"Expected profit: {plan.expected_profit:.4f} {plan.cycle[0]}")
    bot.execute(plan, exchange)
    print("Fill-based positions:", bot.rounded_positions())


if __name__ == "__main__":
    main()

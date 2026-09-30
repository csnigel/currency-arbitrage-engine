# Currency Arbitrage Engine

A dependency-free Python market simulator that models price-time-priority limit order books and detects executable triangular currency arbitrage with a Bellman-Ford negative-cycle search.

This repository is a standalone portfolio edition of an educational financial-computing project. Course-only utilities and assignment harnesses have been replaced with standard-library implementations and an independent test suite.

## How it works

Each currency is a graph node. The best executable bid and ask in every order book create directed conversion edges:

- Selling the base currency at the bid converts base to quote at rate $bid$.
- Buying the base currency at the ask converts quote to base at rate $1/ask$.

For conversion rate $r_{ij}$, the engine assigns edge cost

$$
w_{ij}=-\log(r_{ij}).
$$

A cycle is profitable when its rates multiply to more than one, which is equivalent to a negative total log cost. The engine sizes a detected cycle against the available top-of-book quantity on every leg, creates executable limit orders, and reconciles positions from actual fills.

```mermaid
flowchart LR
    A[Bid and ask books] --> B[Directed conversion graph]
    B --> C[Negative log edge weights]
    C --> D[Bellman-Ford cycle detection]
    D --> E{Profitable cycle?}
    E -- No --> A
    E -- Yes --> F[Liquidity-constrained sizing]
    F --> G[Limit-order execution]
    G --> H[Fill-based positions and PnL]
```

## Features

- Price-time-priority bid and ask queues
- Full and partial fills at the resting order's price
- Multi-pair exchange simulation
- Directed bid/ask conversion graph
- Robust Bellman-Ford negative-cycle reconstruction
- Executable cycle-return calculation
- Top-of-book capacity propagation across every leg
- Fill-based currency position accounting
- Deterministic examples and unit tests

## Installation

```bash
git clone https://github.com/csnigel/currency-arbitrage-engine.git
cd currency-arbitrage-engine
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Run the example

```bash
python examples/run_triangular_arbitrage.py
```

The example seeds three order books with a deliberately inconsistent synthetic quote triangle. Starting from the simulated fills, the bot ends with a positive residual in the cycle's starting currency and zero exposure in the other currencies. It is a correctness demonstration, not a historical return claim.

## Minimal usage

```python
from currency_arbitrage import ArbitrageBot, Exchange, Order, Side

exchange = Exchange([("USD", "EUR"), ("EUR", "GBP"), ("USD", "GBP")])
exchange.submit(Order("USD", "EUR", Side.BUY, price=0.90, quantity=100, timestamp=0))
exchange.submit(Order("EUR", "GBP", Side.BUY, price=0.90, quantity=100, timestamp=0))
exchange.submit(Order("USD", "GBP", Side.SELL, price=0.75, quantity=200, timestamp=0))

bot = ArbitrageBot()
plan = bot.find_plan(exchange.order_books, timestamp=1)
if plan:
    bot.execute(plan, exchange)
    print(bot.positions)
```

## Repository structure

```text
currency-arbitrage-engine/
├── examples/
├── src/currency_arbitrage/
│   ├── models.py          # Orders, fills, and sides
│   ├── order_book.py      # Price-time-priority matching
│   ├── exchange.py        # Multi-pair exchange
│   ├── graph.py           # Conversion graph and negative cycles
│   └── bot.py             # Sizing, execution, and reconciliation
└── tests/
```

## Testing

```bash
python -m pytest -q
```

## Design limitations

- Cycle sizing uses visible top-of-book liquidity rather than multiple depth levels.
- Orders execute synchronously in a deterministic simulator; there is no latency model.
- Fees, minimum order sizes, credit limits, and venue fragmentation are not modeled.
- The engine does not connect to brokers, exchanges, or live market data.

## Disclaimer

This software was developed for educational market simulation. It is not investment advice and is not suitable for live trading without substantial additional validation, risk controls, venue-specific integration, and operational safeguards.

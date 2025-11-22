# Trading Claude

A backtesting system for testing trading strategies against historical stock market data.

## Overview

This system allows you to test various trading strategies using historical data from US stock markets. It helps answer questions like:
- Would buying the highest daily gainers and selling at 5% profit be profitable?
- How do different criteria (market cap, volume, recent performance) affect returns?
- What are the risk-adjusted returns (Sharpe ratio) of different strategies?

## Features

- **Strategy Framework**: Define and test custom trading strategies
- **Historical Data**: Fetch data from Yahoo Finance (free, 5+ years of history)
- **Portfolio Management**: Track multiple positions simultaneously
- **Performance Metrics**: 
  - Total Return
  - Sharpe Ratio
  - Win Rate
  - Maximum Drawdown
  - CAGR (Compound Annual Growth Rate)
  - Sortino Ratio
  - And more...

## Installation

Requires Python 3.10 or higher.

```bash
# Clone the repository
git clone <repository-url>
cd trading-claude

# Install dependencies using PDM
pdm install

# Or using pip
pip install -e .
```

## Quick Start

```python
from trading_claude import run_backtest
from trading_claude.strategies import HighestGainerStrategy

# Run a backtest
results = run_backtest(
    strategy=HighestGainerStrategy(
        gain_threshold=0.05,  # Sell at 5% gain
        max_positions=10,     # Hold up to 10 stocks
    ),
    start_date="2020-01-01",
    end_date="2025-01-01",
    initial_capital=50000,
)

# View results
results.print_summary()
```

## Project Status

🚧 Under active development

## License

MIT License

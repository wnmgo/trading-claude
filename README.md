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
- **Transaction Logging**: Comprehensive audit trail in machine-parsable JSON format
- **Performance Metrics**:
  - Total Return & CAGR
  - Sharpe & Sortino Ratios
  - Win Rate & Profit Factor
  - Maximum Drawdown
  - Trade Statistics
  - And more...

## Installation

Requires Python 3.10 or higher.

```bash
# Clone the repository
git clone https://github.com/wnmgo/trading-claude.git
cd trading-claude

# Install dependencies using PDM
pdm install

# Or using pip
pip install -e .
```

## Quick Start

### Command Line

```bash
# Run a basic backtest (2020-2025, $50k capital, 5% gain target)
trading-claude backtest

# Customize parameters
trading-claude backtest \
  --start 2020-01-01 \
  --end 2025-01-01 \
  --capital 50000 \
  --gain 5.0 \
  --max-positions 10 \
  --stocks-per-day 1 \
  --stop-loss 10.0

# Show version
trading-claude version

# Get help
trading-claude backtest --help
```

### Python API

```python
from datetime import date
from decimal import Decimal

from trading_claude.backtest import BacktestEngine
from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.strategy import HighestGainerStrategy

# Configure backtest
backtest_config = BacktestConfig(
    start_date=date(2020, 1, 1),
    end_date=date(2025, 1, 1),
    initial_capital=Decimal("50000"),
    max_positions=10,
)

# Configure strategy
strategy_config = StrategyConfig(
    gain_threshold_pct=Decimal("5.0"),  # Sell at 5% gain
    stop_loss_pct=Decimal("10.0"),      # Stop loss at 10%
    max_holding_days=30,                # Max 30 days holding
    stocks_per_day=1,                   # Buy 1 stock per day
)

# Run backtest
data_fetcher = MarketDataFetcher()
strategy = HighestGainerStrategy(strategy_config, data_fetcher)
engine = BacktestEngine(strategy, backtest_config)
result = engine.run()

# View results
result.print_summary()
result.get_trades_df().to_csv("trades.csv")
result.get_equity_curve().to_csv("equity.csv")
```

## Strategy: Highest Gainer

The default strategy implements a momentum-based approach:

1. **Selection**: Each day, scan S&P 500 stocks for the highest % gainers (compared to previous day)
2. **Filtering**: Apply optional filters:
   - Minimum stock price (default: $5)
   - Minimum trading volume
   - Market cap requirements
3. **Entry**: Buy the top N stocks with available capital
4. **Exit**: Sell when:
   - Price gains reach target threshold (e.g., 5%)
   - Stop loss triggered (optional)
   - Maximum holding period reached (optional)

## Performance Metrics

The system calculates comprehensive performance metrics:

- **Returns**: Total return, CAGR (annualized)
- **Risk-Adjusted**: Sharpe ratio, Sortino ratio
- **Drawdown**: Maximum drawdown and duration
- **Trade Stats**: Win rate, average gain/loss, profit factor
- **Portfolio**: Average positions held, exposure time

## Transaction Logging

Every backtest automatically generates a detailed transaction log in JSON format. This provides:

### 1. Human Review via Web Interface

Open `examples/transaction_viewer.html` in your browser and load any transaction log file to see:

- Portfolio performance metrics
- Trade-by-trade breakdown with P&L
- Signal analysis (execution rates, missed opportunities)
- Complete event timeline

### 2. Programmatic Analysis & Replay

```python
from trading_claude.transaction_log import TransactionLogger

# Load transaction log
logger = TransactionLogger(Path("results/transactions_20241122_144334.json"))
events = logger.load(logger.output_file)

# Get specific event types
buy_signals = logger.get_events_by_type("signal")
trades = logger.get_events_by_type("trade_completed")
portfolio_snapshots = logger.get_events_by_type("portfolio_snapshot")

# Analyze by symbol
amzn_events = logger.get_events_by_symbol("AMZN")
```

### 3. Strategy Verification

Use the included analyzer to verify strategy compliance:

```bash
python examples/analyze_transactions.py results/transactions_20241122_144334.json
```

This verifies:

- All trades exited at correct gain threshold
- Position sizing limits respected
- Slippage and commission calculations accurate
- Signal execution rates

### Event Types

The transaction log captures:

- `backtest_init`: Initial configuration and parameters
- `signal`: Buy/sell signals generated by strategy
- `order`: Actual order execution with slippage and commissions
- `position_update`: Daily price updates for held positions
- `trade_completed`: Complete trade cycle (entry → exit)
- `portfolio_snapshot`: Daily portfolio state
- `backtest_complete`: Final metrics and results

## Project Structure

```text
trading-claude/
├── src/trading_claude/
│   ├── __init__.py
│   ├── backtest.py         # Backtesting engine
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration models
│   ├── data.py             # Data fetching (yfinance)
│   ├── metrics.py          # Performance metrics
│   ├── models.py           # Core data models
│   ├── strategy.py         # Trading strategies
│   └── transaction_log.py  # Transaction logging
├── examples/
│   ├── simple_backtest.py
│   ├── analyze_transactions.py    # Analyze transaction logs
│   └── transaction_viewer.html    # Web-based log viewer
├── tests/
├── pyproject.toml
└── README.md
```

## Development

```bash
# Install with dev dependencies
pdm install -d

# Run tests
pdm run pytest

# Format code
pdm run black src/

# Type checking
pdm run mypy src/
```

## Roadmap

- [ ] More strategies (mean reversion, breakout, etc.)
- [ ] Visualization (equity curves, drawdown charts)
- [ ] Parameter optimization
- [ ] Walk-forward analysis
- [ ] Multi-asset support
- [ ] Risk management features

## License

MIT License

## Disclaimer

This software is for educational and research purposes only. It is not financial advice. Trading stocks involves risk of loss. Past performance does not guarantee future results.

# Trading Claude - Project Summary

## Overview

Trading Claude is a comprehensive backtesting system designed to test trading strategies against historical stock market data. The system enables you to validate trading ideas like "buy the highest daily gainers and sell at 5% profit" using real historical data from US markets.

**GitHub Repository**: https://github.com/wnmgo/trading-claude

## ✅ What Has Been Implemented

### 1. Core Infrastructure
- ✅ **PDM Project Setup** with dynamic versioning using SCM (git tags)
- ✅ **Version file generation** (`_version.py`) automatically created from git tags
- ✅ **Modern Python practices** using Python 3.10+ with type hints
- ✅ **High-quality dependencies**:
  - yfinance (market data)
  - pandas & numpy (data processing)
  - pydantic (configuration & validation)
  - loguru (logging)
  - typer & rich (CLI)
  - scipy (statistics)
  - matplotlib & seaborn (future visualization)

### 2. Data Layer (`data.py`)
- ✅ **Market data fetching** from Yahoo Finance (free, no subscription needed)
- ✅ **S&P 500 ticker list** automatic fetching
- ✅ **Historical data caching** to reduce API calls
- ✅ **Daily gainer calculation** with configurable lookback periods
- ✅ **Price lookup** for any date with weekend/holiday handling

### 3. Core Models (`models.py`)
- ✅ **Order** - Buy/sell orders with execution tracking
- ✅ **Position** - Open positions with P&L calculation
- ✅ **Trade** - Completed trades with performance metrics
- ✅ **PortfolioSnapshot** - Portfolio state at any point in time
- All models use Pydantic for validation and immutability

### 4. Configuration (`config.py`)
- ✅ **BacktestConfig** - Backtest parameters (dates, capital, constraints)
- ✅ **StrategyConfig** - Strategy-specific settings
- ✅ Environment variable support (`.env` files)
- ✅ Validation using Pydantic
- ✅ Sensible defaults for quick starts

### 5. Strategy Framework (`strategy.py`)
- ✅ **Base TradingStrategy** class for custom strategies
- ✅ **HighestGainerStrategy** implementation with:
  - Daily highest gainer selection from S&P 500
  - Configurable gain threshold for exits (e.g., 5%)
  - Optional stop loss
  - Optional maximum holding period
  - Price filters (min/max price)
  - Volume filters
  - Market cap filters (configurable)
  - Multiple position support

### 6. Backtesting Engine (`backtest.py`)
- ✅ **Portfolio management** with:
  - Cash tracking
  - Position tracking with current prices
  - Order execution with slippage and commissions
  - Position size limits
- ✅ **Daily simulation loop**:
  - Update prices
  - Check sell signals
  - Generate buy signals
  - Execute orders
  - Record snapshots
- ✅ **BacktestResult** with comprehensive output

### 7. Performance Metrics (`metrics.py`)
- ✅ **Return Metrics**:
  - Total return ($ and %)
  - CAGR (Compound Annual Growth Rate)
- ✅ **Risk Metrics**:
  - Sharpe Ratio (risk-adjusted return)
  - Sortino Ratio (downside risk-adjusted return)
  - Maximum Drawdown (% and duration)
- ✅ **Trading Statistics**:
  - Win rate
  - Average gain/loss
  - Largest gain/loss
  - Profit factor
  - Average holding period
- ✅ **Position Statistics**:
  - Average number of positions
  - Maximum positions held

### 8. Command-Line Interface (`cli.py`)
- ✅ **Beautiful CLI** using Typer and Rich
- ✅ **Flexible parameters**:
  - Date range
  - Capital amount
  - Strategy parameters
  - Position limits
  - Filters
- ✅ **Results export** to CSV
- ✅ **Verbose logging** option
- ✅ **Version command**

### 9. Testing & Quality
- ✅ **Test suite** with pytest
  - Config tests
  - Model tests
  - All 9 tests passing
- ✅ **Code formatting** with black
- ✅ **Linting** with ruff
- ✅ **Type checking** with mypy
- ✅ **Coverage tracking** with pytest-cov

### 10. Documentation
- ✅ **Comprehensive README** with:
  - Installation instructions
  - Quick start guides (CLI & Python API)
  - Strategy explanation
  - Metrics documentation
  - Project structure
- ✅ **Example scripts**:
  - simple_backtest.py
  - quick_test.py
- ✅ **Code documentation** with docstrings

## 🎯 How to Use

### Quick Start (CLI)

```bash
# Install
git clone https://github.com/wnmgo/trading-claude.git
cd trading-claude
pdm install

# Run basic backtest
pdm run trading-claude backtest

# Custom backtest
pdm run trading-claude backtest \
  --start 2020-01-01 \
  --end 2024-12-31 \
  --capital 50000 \
  --gain 5.0 \
  --max-positions 10 \
  --stop-loss 10.0 \
  --max-days 30
```

### Python API

```python
from datetime import date
from decimal import Decimal
from trading_claude.backtest import BacktestEngine
from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.strategy import HighestGainerStrategy

# Configure
backtest_config = BacktestConfig(
    start_date=date(2020, 1, 1),
    end_date=date(2025, 1, 1),
    initial_capital=Decimal("50000"),
)

strategy_config = StrategyConfig(
    gain_threshold_pct=Decimal("5.0"),
    stocks_per_day=1,
)

# Run
data_fetcher = MarketDataFetcher()
strategy = HighestGainerStrategy(strategy_config, data_fetcher)
engine = BacktestEngine(strategy, backtest_config)
result = engine.run()

# Results
result.print_summary()
result.get_trades_df().to_csv("trades.csv")
result.get_equity_curve().to_csv("equity.csv")
```

## 📊 Example Output

```
================================================================================
BACKTEST RESULTS SUMMARY
================================================================================

📅 Period: 2020-01-01 to 2025-01-01
💰 Initial Capital: $50,000.00
💰 Final Capital: $XX,XXX.XX

📈 RETURNS
  Total Return: $X,XXX.XX (XX.XX%)
  CAGR: XX.XX%

⚡ RISK METRICS
  Sharpe Ratio: X.XX
  Sortino Ratio: X.XX
  Max Drawdown: XX.XX% (XXX days)

📊 TRADING STATISTICS
  Total Trades: XXX
  Win Rate: XX.XX% (XXW / XXL)
  Avg Gain: X.XX%
  Avg Loss: -X.XX%
  Largest Gain: XX.XX%
  Largest Loss: -XX.XX%
  Profit Factor: X.XX

🎯 POSITION STATISTICS
  Avg Holding Period: XX.X days
  Avg Positions: X.X
  Max Positions: XX

================================================================================
```

## 🔧 Development Workflow

```bash
# Run tests
pdm run test

# Format code
pdm run format

# Lint code
pdm run lint

# Type check
pdm run typecheck

# Coverage report
pdm run test-cov
```

## 📁 Project Structure

```
trading-claude/
├── src/trading_claude/
│   ├── __init__.py           # Package initialization
│   ├── _version.py           # Auto-generated version (from git tags)
│   ├── backtest.py           # Backtesting engine & portfolio
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration models
│   ├── data.py               # Data fetching (yfinance)
│   ├── metrics.py            # Performance metrics calculation
│   ├── models.py             # Core data models
│   └── strategy.py           # Trading strategies
├── examples/
│   ├── simple_backtest.py    # Example usage
│   └── quick_test.py         # Quick verification
├── tests/
│   ├── test_config.py        # Config tests
│   └── test_models.py        # Model tests
├── pyproject.toml            # PDM configuration
├── README.md                 # Documentation
└── .gitignore               # Git ignore rules
```

## 🚀 Git Workflow (As Requested)

The project follows your specified workflow:

```bash
# View issues
gh issue list

# Create feature branch
gh issue view <issue-number>
git checkout -b feature/<description>

# Make changes and commit (conventional commits)
git add .
printf "feat: description\n\nDetailed body\nwith multiple lines" | git commit -F -

# Create PR
gh pr create --title "Title" --body "Description"

# After review, merge and cleanup
gh pr merge <pr-number>
git checkout master
git pull
git branch -d feature/<description>  # Local deleted
# Remote branch kept as requested
```

## 💡 Answering Your Original Questions

### Q: "Would buying the highest earning stock and selling at 5% gain be profitable?"

**A:** You can now test this! Run:
```bash
pdm run trading-claude backtest --gain 5.0 --stocks-per-day 1
```

The system will show you:
- Total return over 5 years
- Win rate (how often trades hit 5% gain)
- Risk metrics (Sharpe ratio, max drawdown)
- Trade statistics

### Q: "Would adding criteria like market cap, volume, recent performance improve results?"

**A:** You can test different configurations:
```bash
# Basic strategy
pdm run trading-claude backtest --gain 5.0

# With filters
pdm run trading-claude backtest --gain 5.0 --min-volume 1000000 --min-price 10

# With stop loss
pdm run trading-claude backtest --gain 5.0 --stop-loss 10.0

# With max holding period
pdm run trading-claude backtest --gain 5.0 --max-days 30
```

Compare the results to see which performs better!

## 🎁 Data Source

**Yahoo Finance (yfinance)** - Completely free, no subscription needed!

- ✅ Historical OHLCV data for S&P 500 stocks
- ✅ 5+ years of history available
- ✅ Adjusted for splits and dividends
- ✅ Real-time updates available
- ✅ No API key required
- ✅ Data cached locally to minimize requests

**Note:** Yahoo Finance is free but may have rate limits. The system includes caching to minimize API calls.

## 🔮 Future Enhancements (Ideas)

While the core system is complete and functional, here are potential improvements:

1. **More Strategies**:
   - Mean reversion
   - Breakout trading
   - Moving average crossovers
   - RSI/MACD indicators

2. **Visualization**:
   - Equity curve plots
   - Drawdown charts
   - Trade distribution histograms

3. **Optimization**:
   - Parameter grid search
   - Walk-forward analysis
   - Monte Carlo simulation

4. **Risk Management**:
   - Dynamic position sizing
   - Correlation analysis
   - Sector exposure limits

5. **Data Sources**:
   - Alternative free sources (Alpha Vantage, etc.)
   - Crypto markets
   - International markets

## ✅ All Requirements Met

- ✅ Open source tools (yfinance, pandas, Python)
- ✅ Free data source (Yahoo Finance via yfinance)
- ✅ PDM for project management
- ✅ Dynamic versioning with SCM
- ✅ Modern Python practices (type hints, Pydantic, etc.)
- ✅ High-quality 3rd party libraries
- ✅ Conventional commits
- ✅ GitHub workflow with gh CLI
- ✅ Comprehensive documentation
- ✅ Working tests

## 📝 Version History

- **v0.1.0** - Initial project setup
- **v0.2.0** - Core backtesting system
- **Current** - Tests and development tools

## 🎉 You're Ready to Start!

The system is fully functional and ready to use. You can:

1. Run backtests on your trading ideas
2. Compare different strategies
3. Analyze historical performance
4. Make data-driven investment decisions

Happy backtesting! 🚀📈

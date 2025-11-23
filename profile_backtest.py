#!/usr/bin/env python3
"""Profile backtest to find performance bottlenecks."""

import cProfile
import pstats
from datetime import date
from decimal import Decimal
from pathlib import Path
from trading_claude.backtest import BacktestEngine
from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.strategy import HighestGainerStrategy

# Small test - 1 week, 5 stocks
config = BacktestConfig(
    initial_capital=Decimal("10000"),
    start_date=date(2024, 6, 1),
    end_date=date(2024, 6, 7),  # Just 1 week
    max_positions=2,
)

strategy_config = StrategyConfig(
    gain_threshold_pct=Decimal("5.0"),
    stocks_per_day=1,
)

# Limit to just 5 tickers for profiling
data_fetcher = MarketDataFetcher(cache_dir=Path("data/cache"))

# Override ticker list to just 5 stocks
original_get_sp500 = data_fetcher.get_sp500_tickers
def get_small_list():
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
data_fetcher.get_sp500_tickers = get_small_list

strategy = HighestGainerStrategy(strategy_config, data_fetcher)
strategy.sp500_tickers = get_small_list()

engine = BacktestEngine(strategy, config)

print("Profiling 1-week backtest with 5 stocks...")
print("=" * 60)

# Profile the run
profiler = cProfile.Profile()
profiler.enable()

result = engine.run()

profiler.disable()

# Print results
print(f"\n{'='*60}")
print(f"RESULTS")
print(f"{'='*60}")
print(f"Final Value: ${result.metrics.final_capital:,.2f}")
print(f"Total Trades: {result.metrics.total_trades}")

# Show top time consumers
print(f"\n{'='*60}")
print(f"TOP TIME CONSUMERS")
print(f"{'='*60}")
stats = pstats.Stats(profiler)
stats.strip_dirs()
stats.sort_stats('cumulative')
stats.print_stats(30)  # Top 30 functions by cumulative time

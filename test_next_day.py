#!/usr/bin/env python3
"""Quick test to verify next-day execution works."""

from datetime import date
from decimal import Decimal
from pathlib import Path
from trading_claude.backtest import BacktestEngine
from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.strategy import HighestGainerStrategy

# Test with just 2 weeks to verify the logic works
config = BacktestConfig(
    initial_capital=Decimal("10000"),
    start_date=date(2024, 6, 1),
    end_date=date(2024, 6, 14),
    max_positions=2,
)

strategy_config = StrategyConfig(
    gain_threshold_pct=Decimal("5.0"),
    stocks_per_day=1,
)

data_fetcher = MarketDataFetcher(cache_dir=Path("data/cache"))
strategy = HighestGainerStrategy(strategy_config, data_fetcher)
engine = BacktestEngine(strategy, config)

print("Running 2-week backtest to verify next-day execution...")
result = engine.run()

print(f"\n{'='*60}")
print(f"BACKTEST RESULTS")
print(f"{'='*60}")
print(f"Final Value: ${result.metrics.final_capital:,.2f}")
print(f"Total Return: {result.metrics.total_return_pct:.2f}%")
print(f"Total Trades: {result.metrics.total_trades}")
print(f"Win Rate: {result.metrics.win_rate:.1f}%")

# Show all trades to verify timing
print(f"\n{'='*60}")
print(f"ALL TRADES (verifying signal date != execution date)")
print(f"{'='*60}")
for i, trade in enumerate(result.trades, 1):
    holding_days = (trade.exit_date - trade.entry_date).days
    print(f"\nTrade {i}:")
    print(f"  Symbol: {trade.symbol}")
    print(f"  Entry: {trade.entry_date.date()} @ ${trade.entry_price:.2f}")
    print(f"  Exit:  {trade.exit_date.date()} @ ${trade.exit_price:.2f}")
    print(f"  P&L: {trade.pnl_pct:+.2f}% (${trade.pnl:+.2f})")
    print(f"  Holding: {holding_days} days")

if result.metrics.total_trades == 0:
    print("\nNo trades executed - this might indicate an issue!")
else:
    print(f"\n✓ Test completed successfully with {result.metrics.total_trades} trade(s)")

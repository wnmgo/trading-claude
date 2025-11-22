"""Quick test script to verify the system works."""

from datetime import date
from decimal import Decimal

from trading_claude.backtest import BacktestEngine
from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.strategy import HighestGainerStrategy


def test_quick():
    """Quick test with a short time period."""
    print("🧪 Running quick test...\n")

    # Very short test period
    backtest_config = BacktestConfig(
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 31),
        initial_capital=Decimal("10000"),
        max_positions=3,
    )

    strategy_config = StrategyConfig(
        gain_threshold_pct=Decimal("5.0"),
        stocks_per_day=1,
        lookback_days=1,
    )

    # Run test
    data_fetcher = MarketDataFetcher()
    strategy = HighestGainerStrategy(strategy_config, data_fetcher)
    engine = BacktestEngine(strategy, backtest_config)

    result = engine.run()
    result.print_summary()

    print("✅ Test complete!\n")


if __name__ == "__main__":
    test_quick()

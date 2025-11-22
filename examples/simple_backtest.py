"""Example: Running a simple backtest."""

from datetime import date
from decimal import Decimal

from loguru import logger

from trading_claude.backtest import BacktestEngine
from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.strategy import HighestGainerStrategy


def main():
    """Run a simple backtest example."""
    # Configure logging
    logger.add("backtest.log", rotation="10 MB")

    print("🚀 Trading Claude - Example Backtest\n")

    # Create configurations
    backtest_config = BacktestConfig(
        start_date=date(2020, 1, 1),
        end_date=date(2025, 1, 1),
        initial_capital=Decimal("50000"),
        max_positions=10,
    )

    strategy_config = StrategyConfig(
        gain_threshold_pct=Decimal("5.0"),  # Sell at 5% gain
        stop_loss_pct=Decimal("10.0"),  # Stop loss at 10% loss
        max_holding_days=30,  # Max 30 days holding
        min_price=Decimal("5.0"),  # Min $5 stock price
        lookback_days=1,  # Daily gainers
        stocks_per_day=1,  # Buy 1 stock per day
    )

    # Initialize components
    data_fetcher = MarketDataFetcher()
    strategy = HighestGainerStrategy(strategy_config, data_fetcher)
    engine = BacktestEngine(strategy, backtest_config)

    # Run backtest
    print("Running backtest...\n")
    result = engine.run()

    # Print results
    result.print_summary()

    # Save results
    print("Saving results...")
    result.get_trades_df().to_csv("trades.csv", index=False)
    result.get_equity_curve().to_csv("equity_curve.csv", index=False)
    print("✓ Results saved to trades.csv and equity_curve.csv\n")


if __name__ == "__main__":
    main()

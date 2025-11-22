"""Test configuration models."""

from datetime import date
from decimal import Decimal

import pytest

from trading_claude.config import BacktestConfig, StrategyConfig


def test_backtest_config_defaults():
    """Test BacktestConfig default values."""
    config = BacktestConfig()
    assert config.initial_capital == Decimal("50000")
    assert config.max_positions == 10
    assert config.commission_per_trade == Decimal("0")
    assert config.slippage_pct == Decimal("0.1")


def test_backtest_config_custom():
    """Test BacktestConfig with custom values."""
    config = BacktestConfig(
        start_date=date(2020, 1, 1),
        end_date=date(2021, 1, 1),
        initial_capital=Decimal("100000"),
        max_positions=5,
    )
    assert config.start_date == date(2020, 1, 1)
    assert config.end_date == date(2021, 1, 1)
    assert config.initial_capital == Decimal("100000")
    assert config.max_positions == 5


def test_strategy_config_defaults():
    """Test StrategyConfig default values."""
    config = StrategyConfig()
    assert config.gain_threshold_pct == Decimal("5.0")
    assert config.lookback_days == 1
    assert config.stocks_per_day == 1
    assert config.min_price == Decimal("5.0")


def test_strategy_config_custom():
    """Test StrategyConfig with custom values."""
    config = StrategyConfig(
        gain_threshold_pct=Decimal("10.0"),
        stop_loss_pct=Decimal("5.0"),
        max_holding_days=30,
        stocks_per_day=2,
    )
    assert config.gain_threshold_pct == Decimal("10.0")
    assert config.stop_loss_pct == Decimal("5.0")
    assert config.max_holding_days == 30
    assert config.stocks_per_day == 2

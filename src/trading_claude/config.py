"""Configuration management using Pydantic."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BacktestConfig(BaseSettings):
    """Configuration for backtesting."""

    # Time period
    start_date: date = Field(
        default_factory=lambda: date(2020, 1, 1),
        description="Start date for backtest",
    )
    end_date: date = Field(
        default_factory=lambda: date.today(),
        description="End date for backtest",
    )

    # Capital
    initial_capital: Decimal = Field(
        default=Decimal("50000"),
        gt=0,
        description="Initial capital in USD",
    )

    # Portfolio constraints
    max_positions: int = Field(
        default=10,
        gt=0,
        description="Maximum number of positions to hold simultaneously",
    )
    max_position_size_pct: Decimal = Field(
        default=Decimal("20"),
        gt=0,
        le=100,
        description="Maximum position size as percentage of portfolio value",
    )

    # Trading costs
    commission_per_trade: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Commission per trade in USD",
    )
    slippage_pct: Decimal = Field(
        default=Decimal("0.1"),
        ge=0,
        description="Slippage as percentage of trade value",
    )

    # Data settings
    data_cache_dir: Path = Field(
        default=Path("data/cache"),
        description="Directory to cache market data",
    )

    model_config = SettingsConfigDict(
        env_prefix="BACKTEST_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class StrategyConfig(BaseSettings):
    """Configuration for trading strategies."""

    # Strategy type
    strategy_name: str = Field(
        default="HighestGainerStrategy",
        description="Name of the strategy to use",
    )

    # Highest Gainer Strategy settings
    gain_threshold_pct: Decimal = Field(
        default=Decimal("5.0"),
        gt=0,
        description="Sell when position gains this percentage",
    )
    stop_loss_pct: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Stop loss percentage (optional)",
    )
    max_holding_days: Optional[int] = Field(
        default=None,
        gt=0,
        description="Maximum holding period in days (optional)",
    )

    # Selection criteria
    min_market_cap: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Minimum market cap in USD (optional)",
    )
    min_volume: Optional[int] = Field(
        default=None,
        gt=0,
        description="Minimum daily trading volume (optional)",
    )
    min_price: Decimal = Field(
        default=Decimal("5.0"),
        gt=0,
        description="Minimum stock price",
    )
    max_price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Maximum stock price (optional)",
    )

    # Lookback period for "highest gainer"
    lookback_days: int = Field(
        default=1,
        gt=0,
        description="Number of days to look back for gain calculation",
    )

    # Number of stocks to buy each day
    stocks_per_day: int = Field(
        default=1,
        gt=0,
        description="Number of stocks to buy each trading day",
    )

    model_config = SettingsConfigDict(
        env_prefix="STRATEGY_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

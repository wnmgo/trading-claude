"""Base strategy class and implementations."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Optional

from loguru import logger

from trading_claude.config import StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.models import Position


class TradingStrategy(ABC):
    """Abstract base class for trading strategies."""

    def __init__(self, config: StrategyConfig, data_fetcher: MarketDataFetcher):
        """Initialize the strategy.

        Args:
            config: Strategy configuration
            data_fetcher: Market data fetcher
        """
        self.config = config
        self.data_fetcher = data_fetcher

    @abstractmethod
    def generate_signals(
        self,
        current_date: datetime,
        cash_available: Decimal,
        current_positions: list[Position],
        max_positions: int = 10,
    ) -> list[tuple[str, int]]:
        """Generate buy signals for the current date.

        Args:
            current_date: Current trading date
            cash_available: Available cash for trading
            current_positions: Current open positions

        Returns:
            List of (symbol, shares) tuples to buy
        """
        pass

    @abstractmethod
    def should_sell(
        self,
        position: Position,
        current_date: datetime,
    ) -> bool:
        """Determine if a position should be sold.

        Args:
            position: Position to check
            current_date: Current trading date

        Returns:
            True if position should be sold
        """
        pass


class HighestGainerStrategy(TradingStrategy):
    """Strategy that buys the highest daily gainers and sells at target profit."""

    def __init__(self, config: StrategyConfig, data_fetcher: MarketDataFetcher):
        """Initialize the highest gainer strategy.

        Args:
            config: Strategy configuration
            data_fetcher: Market data fetcher
        """
        super().__init__(config, data_fetcher)
        self.sp500_tickers = data_fetcher.get_sp500_tickers()
        logger.info(f"Initialized HighestGainerStrategy with {len(self.sp500_tickers)} tickers")

    def generate_signals(
        self,
        current_date: datetime,
        cash_available: Decimal,
        current_positions: list[Position],
        max_positions: int = 10,
    ) -> list[tuple[str, int]]:
        """Generate buy signals by selecting highest gainers.

        Args:
            current_date: Current trading date
            cash_available: Available cash for trading
            current_positions: Current open positions
            max_positions: Maximum number of positions allowed

        Returns:
            List of (symbol, shares) tuples to buy
        """
        # Check if we can buy more positions
        num_current_positions = len(current_positions)
        
        if num_current_positions >= max_positions:
            logger.debug(f"Already at max positions ({max_positions})")
            return []

        # Get highest gainers
        gainers_df = self.data_fetcher.get_daily_gainers(
            self.sp500_tickers,
            current_date,
            self.config.lookback_days,
        )

        if gainers_df.empty:
            logger.debug(f"No gainers found for {current_date.date()}")
            return []

        # Apply filters
        filtered_df = gainers_df.copy()

        # Price filters
        filtered_df = filtered_df[filtered_df["price"] >= float(self.config.min_price)]
        if self.config.max_price:
            filtered_df = filtered_df[filtered_df["price"] <= float(self.config.max_price)]

        # Volume filter
        if self.config.min_volume:
            filtered_df = filtered_df[filtered_df["volume"] >= self.config.min_volume]

        # Remove stocks we already own
        current_symbols = {pos.symbol for pos in current_positions}
        filtered_df = filtered_df[~filtered_df["symbol"].isin(current_symbols)]

        if filtered_df.empty:
            logger.debug("No stocks passed filters")
            return []

        # Select top N stocks
        stocks_to_buy = min(
            self.config.stocks_per_day,
            max_positions - num_current_positions,
            len(filtered_df),
        )

        signals = []
        cash_per_stock = cash_available / stocks_to_buy

        for i in range(stocks_to_buy):
            row = filtered_df.iloc[i]
            symbol = row["symbol"]
            price = Decimal(str(row["price"]))

            # Calculate shares to buy
            shares = int(cash_per_stock / price)
            
            if shares > 0:
                signals.append((symbol, shares))
                logger.info(
                    f"Buy signal: {symbol} @ ${price:.2f}, "
                    f"{shares} shares, gain: {row['gain_pct']:.2f}%"
                )

        return signals

    def should_sell(
        self,
        position: Position,
        current_date: datetime,
    ) -> bool:
        """Determine if position should be sold based on gain threshold.

        Args:
            position: Position to check
            current_date: Current trading date

        Returns:
            True if position should be sold
        """
        # Update position price
        current_price = self.data_fetcher.get_price_at_date(
            position.symbol, current_date
        )

        if current_price is None:
            logger.warning(f"Could not get price for {position.symbol}")
            return False

        position = position.update_price(current_price)

        # Check gain threshold
        if position.unrealized_pnl_pct >= self.config.gain_threshold_pct:
            logger.info(
                f"Sell signal: {position.symbol} hit gain target "
                f"({position.unrealized_pnl_pct:.2f}% >= {self.config.gain_threshold_pct}%)"
            )
            return True

        # Check stop loss
        if self.config.stop_loss_pct:
            if position.unrealized_pnl_pct <= -self.config.stop_loss_pct:
                logger.info(
                    f"Sell signal: {position.symbol} hit stop loss "
                    f"({position.unrealized_pnl_pct:.2f}% <= -{self.config.stop_loss_pct}%)"
                )
                return True

        # Check max holding period
        if self.config.max_holding_days:
            holding_days = (current_date - position.entry_date).days
            if holding_days >= self.config.max_holding_days:
                logger.info(
                    f"Sell signal: {position.symbol} hit max holding period "
                    f"({holding_days} >= {self.config.max_holding_days} days)"
                )
                return True

        return False

"""Backtesting engine for trading strategies."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import pandas as pd
from loguru import logger

from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.metrics import PerformanceMetrics, calculate_metrics
from trading_claude.models import Order, OrderType, Position, PortfolioSnapshot, Trade
from trading_claude.strategy import HighestGainerStrategy, TradingStrategy


class Portfolio:
    """Manages portfolio state during backtesting."""

    def __init__(self, initial_capital: Decimal, config: BacktestConfig):
        """Initialize portfolio.

        Args:
            initial_capital: Starting capital
            config: Backtest configuration
        """
        self.initial_capital = initial_capital
        self.config = config
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.snapshots: list[PortfolioSnapshot] = []

    @property
    def positions_value(self) -> Decimal:
        """Total value of all positions."""
        return sum(pos.current_value for pos in self.positions.values())

    @property
    def total_value(self) -> Decimal:
        """Total portfolio value (cash + positions)."""
        return self.cash + self.positions_value

    def buy(
        self,
        symbol: str,
        shares: int,
        price: Decimal,
        timestamp: datetime,
    ) -> bool:
        """Execute a buy order.

        Args:
            symbol: Stock symbol
            shares: Number of shares
            price: Price per share
            timestamp: Execution timestamp

        Returns:
            True if order executed successfully
        """
        # Calculate total cost including slippage and commission
        slippage = price * self.config.slippage_pct / 100
        execution_price = price + slippage
        total_cost = execution_price * shares + self.config.commission_per_trade

        if total_cost > self.cash:
            logger.warning(
                f"Insufficient cash to buy {shares} shares of {symbol} "
                f"(need ${total_cost:.2f}, have ${self.cash:.2f})"
            )
            return False

        # Check position size limit
        max_position_value = self.total_value * self.config.max_position_size_pct / 100
        if execution_price * shares > max_position_value:
            # Adjust shares to fit within limit
            shares = int(max_position_value / execution_price)
            if shares == 0:
                logger.warning(
                    f"Position size limit prevents buying {symbol}"
                )
                return False
            total_cost = execution_price * shares + self.config.commission_per_trade

        # Execute order
        self.cash -= total_cost

        # Add or update position
        if symbol in self.positions:
            # Average in if we already have a position
            old_pos = self.positions[symbol]
            new_shares = old_pos.shares + shares
            new_cost_basis = old_pos.cost_basis + (execution_price * shares)
            new_entry_price = new_cost_basis / new_shares

            self.positions[symbol] = Position(
                symbol=symbol,
                shares=new_shares,
                entry_price=new_entry_price,
                entry_date=old_pos.entry_date,  # Keep original entry date
                current_price=execution_price,
            )
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                shares=shares,
                entry_price=execution_price,
                entry_date=timestamp,
                current_price=execution_price,
            )

        logger.info(
            f"BUY {shares} {symbol} @ ${execution_price:.2f} "
            f"(total: ${total_cost:.2f}, cash remaining: ${self.cash:.2f})"
        )
        return True

    def sell(
        self,
        symbol: str,
        timestamp: datetime,
        price: Optional[Decimal] = None,
    ) -> bool:
        """Execute a sell order for entire position.

        Args:
            symbol: Stock symbol
            timestamp: Execution timestamp
            price: Override price (if None, uses current position price)

        Returns:
            True if order executed successfully
        """
        if symbol not in self.positions:
            logger.warning(f"Cannot sell {symbol}: no position exists")
            return False

        position = self.positions[symbol]
        sell_price = price or position.current_price

        if sell_price is None:
            logger.error(f"Cannot sell {symbol}: no price available")
            return False

        # Apply slippage (negative for sells)
        slippage = sell_price * self.config.slippage_pct / 100
        execution_price = sell_price - slippage

        # Calculate proceeds
        proceeds = execution_price * position.shares - self.config.commission_per_trade

        # Update cash
        self.cash += proceeds

        # Record trade
        trade = Trade(
            symbol=symbol,
            entry_date=position.entry_date,
            exit_date=timestamp,
            entry_price=position.entry_price,
            exit_price=execution_price,
            shares=position.shares,
            pnl=proceeds - position.cost_basis,
            pnl_pct=position.unrealized_pnl_pct,
            holding_days=(timestamp - position.entry_date).days,
        )
        self.trades.append(trade)

        logger.info(
            f"SELL {position.shares} {symbol} @ ${execution_price:.2f} "
            f"(PnL: ${trade.pnl:.2f} / {trade.pnl_pct:.2f}%, "
            f"held {trade.holding_days} days)"
        )

        # Remove position
        del self.positions[symbol]
        return True

    def update_prices(self, date: datetime, data_fetcher: MarketDataFetcher):
        """Update current prices for all positions.

        Args:
            date: Current date
            data_fetcher: Market data fetcher
        """
        for symbol in list(self.positions.keys()):
            price = data_fetcher.get_price_at_date(symbol, date)
            if price is not None:
                self.positions[symbol] = self.positions[symbol].update_price(price)

    def take_snapshot(self, timestamp: datetime):
        """Record current portfolio state.

        Args:
            timestamp: Snapshot timestamp
        """
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            cash=self.cash,
            positions_value=self.positions_value,
            total_value=self.total_value,
            positions=list(self.positions.values()),
        )
        self.snapshots.append(snapshot)


class BacktestEngine:
    """Runs backtests on trading strategies."""

    def __init__(
        self,
        strategy: TradingStrategy,
        backtest_config: BacktestConfig,
    ):
        """Initialize backtest engine.

        Args:
            strategy: Trading strategy to test
            backtest_config: Backtest configuration
        """
        self.strategy = strategy
        self.config = backtest_config
        self.portfolio = Portfolio(backtest_config.initial_capital, backtest_config)

    def run(self) -> "BacktestResult":
        """Run the backtest.

        Returns:
            Backtest results
        """
        logger.info(
            f"Starting backtest from {self.config.start_date} to {self.config.end_date}"
        )
        logger.info(f"Initial capital: ${self.config.initial_capital}")

        # Generate trading days
        current_date = datetime.combine(self.config.start_date, datetime.min.time())
        end_date = datetime.combine(self.config.end_date, datetime.min.time())

        while current_date <= end_date:
            # Update position prices
            self.portfolio.update_prices(
                current_date, self.strategy.data_fetcher
            )

            # Check for sell signals
            for symbol in list(self.portfolio.positions.keys()):
                position = self.portfolio.positions[symbol]
                if self.strategy.should_sell(position, current_date):
                    self.portfolio.sell(symbol, current_date)

            # Generate buy signals
            buy_signals = self.strategy.generate_signals(
                current_date,
                self.portfolio.cash,
                list(self.portfolio.positions.values()),
            )

            # Execute buy orders
            for symbol, shares in buy_signals:
                price = self.strategy.data_fetcher.get_price_at_date(
                    symbol, current_date
                )
                if price:
                    self.portfolio.buy(symbol, shares, price, current_date)

            # Take snapshot
            self.portfolio.take_snapshot(current_date)

            # Move to next day
            current_date += timedelta(days=1)

        logger.info("Backtest complete")
        logger.info(f"Final portfolio value: ${self.portfolio.total_value:.2f}")
        logger.info(f"Total trades: {len(self.portfolio.trades)}")

        # Calculate metrics
        metrics = calculate_metrics(
            self.portfolio.snapshots,
            self.portfolio.trades,
            self.config.initial_capital,
        )

        return BacktestResult(
            metrics=metrics,
            trades=self.portfolio.trades,
            snapshots=self.portfolio.snapshots,
            config=self.config,
        )


class BacktestResult:
    """Results from a backtest run."""

    def __init__(
        self,
        metrics: PerformanceMetrics,
        trades: list[Trade],
        snapshots: list[PortfolioSnapshot],
        config: BacktestConfig,
    ):
        """Initialize backtest results.

        Args:
            metrics: Performance metrics
            trades: List of completed trades
            snapshots: List of portfolio snapshots
            config: Backtest configuration
        """
        self.metrics = metrics
        self.trades = trades
        self.snapshots = snapshots
        self.config = config

    def print_summary(self):
        """Print a summary of the backtest results."""
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS SUMMARY")
        print("=" * 80)

        print(f"\n📅 Period: {self.config.start_date} to {self.config.end_date}")
        print(f"💰 Initial Capital: ${self.metrics.initial_capital:,.2f}")
        print(f"💰 Final Capital: ${self.metrics.final_capital:,.2f}")

        print("\n📈 RETURNS")
        print(f"  Total Return: ${self.metrics.total_return:,.2f} ({self.metrics.total_return_pct:.2f}%)")
        print(f"  CAGR: {self.metrics.cagr:.2f}%")

        print("\n⚡ RISK METRICS")
        print(f"  Sharpe Ratio: {self.metrics.sharpe_ratio:.2f}" if self.metrics.sharpe_ratio else "  Sharpe Ratio: N/A")
        print(f"  Sortino Ratio: {self.metrics.sortino_ratio:.2f}" if self.metrics.sortino_ratio else "  Sortino Ratio: N/A")
        print(f"  Max Drawdown: {self.metrics.max_drawdown:.2f}% ({self.metrics.max_drawdown_duration} days)")

        print("\n📊 TRADING STATISTICS")
        print(f"  Total Trades: {self.metrics.total_trades}")
        print(f"  Win Rate: {self.metrics.win_rate:.2f}% ({self.metrics.winning_trades}W / {self.metrics.losing_trades}L)")
        print(f"  Avg Gain: {self.metrics.avg_gain:.2f}%")
        print(f"  Avg Loss: {self.metrics.avg_loss:.2f}%")
        print(f"  Largest Gain: {self.metrics.largest_gain:.2f}%")
        print(f"  Largest Loss: {self.metrics.largest_loss:.2f}%")
        print(f"  Profit Factor: {self.metrics.profit_factor:.2f}" if self.metrics.profit_factor else "  Profit Factor: N/A")

        print("\n🎯 POSITION STATISTICS")
        print(f"  Avg Holding Period: {self.metrics.avg_holding_days:.1f} days")
        print(f"  Avg Positions: {self.metrics.avg_num_positions:.1f}")
        print(f"  Max Positions: {self.metrics.max_num_positions}")

        print("\n" + "=" * 80 + "\n")

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as a pandas DataFrame.

        Returns:
            DataFrame with trade data
        """
        if not self.trades:
            return pd.DataFrame()

        return pd.DataFrame([trade.model_dump() for trade in self.trades])

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as a pandas DataFrame.

        Returns:
            DataFrame with timestamp and portfolio value
        """
        if not self.snapshots:
            return pd.DataFrame()

        return pd.DataFrame(
            {
                "timestamp": [s.timestamp for s in self.snapshots],
                "total_value": [float(s.total_value) for s in self.snapshots],
                "cash": [float(s.cash) for s in self.snapshots],
                "positions_value": [float(s.positions_value) for s in self.snapshots],
            }
        )

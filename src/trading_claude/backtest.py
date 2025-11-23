"""Backtesting engine for trading strategies."""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.metrics import PerformanceMetrics, calculate_metrics
from trading_claude.models import Order, OrderType, Position, PortfolioSnapshot, Trade
from trading_claude.strategy import HighestGainerStrategy, TradingStrategy
from trading_claude.transaction_log import (
    BacktestCompleteEvent,
    BacktestInitEvent,
    OrderEvent,
    PortfolioSnapshotEvent,
    PositionUpdateEvent,
    SignalEvent,
    TradeCompletedEvent,
    TransactionLogger,
)


class Portfolio:
    """Manages portfolio state during backtesting."""

    def __init__(
        self, 
        initial_capital: Decimal, 
        config: BacktestConfig,
        transaction_logger: Optional[TransactionLogger] = None,
    ):
        """Initialize portfolio.

        Args:
            initial_capital: Starting capital
            config: Backtest configuration
            transaction_logger: Optional transaction logger
        """
        self.initial_capital = initial_capital
        self.config = config
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.snapshots: list[PortfolioSnapshot] = []
        self.transaction_logger = transaction_logger

    @property
    def positions_value(self) -> Decimal:
        """Total value of all positions."""
        return sum((pos.current_value for pos in self.positions.values()), Decimal("0"))

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
        cash_before = self.cash
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

        # Log transaction
        if self.transaction_logger:
            self.transaction_logger.log(OrderEvent(
                timestamp=timestamp,
                order_type=OrderType.BUY,
                symbol=symbol,
                shares=shares,
                target_price=price,
                actual_price=execution_price,
                slippage=slippage,
                commission=self.config.commission_per_trade,
                total_cost=total_cost,
                cash_before=cash_before,
                cash_after=self.cash,
            ))

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
        cash_before = self.cash
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

        # Log transaction
        if self.transaction_logger:
            self.transaction_logger.log(OrderEvent(
                timestamp=timestamp,
                order_type=OrderType.SELL,
                symbol=symbol,
                shares=position.shares,
                target_price=sell_price,
                actual_price=execution_price,
                slippage=slippage,
                commission=self.config.commission_per_trade,
                total_cost=proceeds,
                cash_before=cash_before,
                cash_after=self.cash,
            ))
            
            self.transaction_logger.log(TradeCompletedEvent(
                timestamp=timestamp,
                symbol=symbol,
                entry_date=position.entry_date,
                exit_date=timestamp,
                entry_price=position.entry_price,
                exit_price=execution_price,
                shares=position.shares,
                pnl=trade.pnl,
                pnl_pct=trade.pnl_pct,
                holding_days=trade.holding_days,
                total_cost=position.cost_basis,
                total_proceeds=proceeds,
            ))

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
                old_position = self.positions[symbol]
                self.positions[symbol] = old_position.update_price(price)
                
                # Log position update
                if self.transaction_logger:
                    updated_position = self.positions[symbol]
                    self.transaction_logger.log(PositionUpdateEvent(
                        timestamp=date,
                        symbol=symbol,
                        shares=updated_position.shares,
                        entry_price=updated_position.entry_price,
                        entry_date=updated_position.entry_date,
                        current_price=price,
                        unrealized_pnl=updated_position.unrealized_pnl,
                        unrealized_pnl_pct=updated_position.unrealized_pnl_pct,
                    ))

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
        
        # Log portfolio snapshot
        if self.transaction_logger:
            positions_data = [
                {
                    "symbol": pos.symbol,
                    "shares": pos.shares,
                    "entry_price": str(pos.entry_price),
                    "current_price": str(pos.current_price) if pos.current_price else None,
                    "unrealized_pnl": str(pos.unrealized_pnl),
                    "unrealized_pnl_pct": str(pos.unrealized_pnl_pct),
                }
                for pos in self.positions.values()
            ]
            
            self.transaction_logger.log(PortfolioSnapshotEvent(
                timestamp=timestamp,
                cash=self.cash,
                positions_value=self.positions_value,
                total_value=self.total_value,
                num_positions=len(self.positions),
                positions=positions_data,
            ))


class BacktestEngine:
    """Runs backtests on trading strategies."""

    def __init__(
        self,
        strategy: TradingStrategy,
        backtest_config: BacktestConfig,
        transaction_log_file: Optional[Path] = None,
    ):
        """Initialize backtest engine.

        Args:
            strategy: Trading strategy to test
            backtest_config: Backtest configuration
            transaction_log_file: Optional path for transaction log file
        """
        self.strategy = strategy
        self.config = backtest_config
        self.transaction_logger = (
            TransactionLogger(transaction_log_file) if transaction_log_file else None
        )
        self.portfolio = Portfolio(
            backtest_config.initial_capital, 
            backtest_config,
            self.transaction_logger,
        )
        self.pending_signals: list[tuple[str, int, datetime]] = []  # (symbol, shares, signal_date)

    def run(self) -> "BacktestResult":
        """Run the backtest.

        Returns:
            Backtest results
        """
        logger.info(
            f"Starting backtest from {self.config.start_date} to {self.config.end_date}"
        )
        logger.info(f"Initial capital: ${self.config.initial_capital}")

        # Log backtest initialization
        if self.transaction_logger:
            self.transaction_logger.log(BacktestInitEvent(
                timestamp=datetime.now(),
                initial_capital=self.config.initial_capital,
                start_date=datetime.combine(self.config.start_date, datetime.min.time()),
                end_date=datetime.combine(self.config.end_date, datetime.min.time()),
                strategy_name=self.strategy.__class__.__name__,
                strategy_config=self.strategy.config.model_dump() if hasattr(self.strategy, 'config') else {},
                backtest_config=self.config.model_dump(),
            ))

        # Generate trading days
        current_date = datetime.combine(self.config.start_date, datetime.min.time())
        end_date = datetime.combine(self.config.end_date, datetime.min.time())

        while current_date <= end_date:
            # Step 1: Execute pending buy signals from YESTERDAY at TODAY's OPEN price
            # This eliminates look-ahead bias
            if self.pending_signals:
                executed_signals = []
                for symbol, shares, signal_date in self.pending_signals:
                    open_price = self.strategy.data_fetcher.get_open_price(
                        symbol, current_date
                    )
                    if open_price:
                        success = self.portfolio.buy(symbol, shares, open_price, current_date)
                        if success:
                            executed_signals.append((symbol, shares, signal_date))
                            logger.info(
                                f"Executed buy: {symbol} {shares} shares @ ${open_price:.2f} "
                                f"(signal from {signal_date.date()})"
                            )
                    else:
                        logger.warning(
                            f"Could not get open price for {symbol} on {current_date.date()}, "
                            f"order not executed"
                        )
                
                # Clear executed signals
                self.pending_signals = []
            
            # Step 2: Update position prices
            self.portfolio.update_prices(
                current_date, self.strategy.data_fetcher
            )

            # Step 3: Check for sell signals and execute immediately
            for symbol in list(self.portfolio.positions.keys()):
                position = self.portfolio.positions[symbol]
                should_sell_result = self.strategy.should_sell(position, current_date)
                
                if should_sell_result:
                    # Log sell signal
                    if self.transaction_logger:
                        self.transaction_logger.log(SignalEvent(
                            timestamp=current_date,
                            signal_type="sell",
                            symbol=symbol,
                            price=position.current_price or position.entry_price,
                            shares=position.shares,
                            reason=f"Gain target hit: {position.unrealized_pnl_pct:.2f}%",
                            metadata={
                                "unrealized_pnl": str(position.unrealized_pnl),
                                "unrealized_pnl_pct": str(position.unrealized_pnl_pct),
                                "holding_days": (current_date - position.entry_date).days,
                            }
                        ))
                    
                    self.portfolio.sell(symbol, current_date)

            # Step 4: Generate buy signals for TOMORROW's execution
            buy_signals = self.strategy.generate_signals(
                current_date,
                self.portfolio.cash,
                list(self.portfolio.positions.values()),
                self.config.max_positions,
            )

            # Step 5: Log signals and queue for tomorrow's execution
            for symbol, shares in buy_signals:
                # Get closing price for logging purposes only
                close_price = self.strategy.data_fetcher.get_price_at_date(
                    symbol, current_date
                )
                if close_price:
                    # Log buy signal
                    if self.transaction_logger:
                        self.transaction_logger.log(SignalEvent(
                            timestamp=current_date,
                            signal_type="buy",
                            symbol=symbol,
                            price=close_price,
                            shares=shares,
                            reason="Highest gainer signal - will execute at next day's open",
                            metadata={"execution_date": str((current_date + timedelta(days=1)).date())}
                        ))
                    
                    # Queue for tomorrow's execution
                    self.pending_signals.append((symbol, shares, current_date))
                    logger.info(
                        f"Buy signal: {symbol} {shares} shares @ ${close_price:.2f} "
                        f"(will execute at tomorrow's open)"
                    )

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

        # Log backtest completion
        if self.transaction_logger:
            self.transaction_logger.log(BacktestCompleteEvent(
                timestamp=datetime.now(),
                final_capital=self.portfolio.total_value,
                total_return=metrics.total_return,
                total_return_pct=metrics.total_return_pct,
                total_trades=metrics.total_trades,
                winning_trades=metrics.winning_trades,
                losing_trades=metrics.losing_trades,
                win_rate=metrics.win_rate,
                metrics=metrics.model_dump(),
            ))
            
            # Save transaction log
            self.transaction_logger.save()
            logger.info(f"Transaction log saved to: {self.transaction_logger.output_file}")

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

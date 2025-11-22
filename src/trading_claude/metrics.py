"""Performance metrics calculation."""

from decimal import Decimal
from typing import Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from trading_claude.models import PortfolioSnapshot, Trade


class PerformanceMetrics(BaseModel):
    """Performance metrics for backtesting results."""

    # Returns
    total_return: Decimal = Field(description="Total return in dollars")
    total_return_pct: Decimal = Field(description="Total return percentage")
    cagr: Decimal = Field(description="Compound Annual Growth Rate (%)")

    # Risk metrics
    sharpe_ratio: Optional[Decimal] = Field(
        default=None, description="Sharpe ratio (risk-adjusted return)"
    )
    sortino_ratio: Optional[Decimal] = Field(
        default=None, description="Sortino ratio (downside risk-adjusted return)"
    )
    max_drawdown: Decimal = Field(description="Maximum drawdown (%)")
    max_drawdown_duration: int = Field(
        description="Maximum drawdown duration in days"
    )

    # Trading statistics
    total_trades: int = Field(description="Total number of trades")
    winning_trades: int = Field(description="Number of winning trades")
    losing_trades: int = Field(description="Number of losing trades")
    win_rate: Decimal = Field(description="Win rate (%)")

    # Trade performance
    avg_gain: Decimal = Field(description="Average gain per trade (%)")
    avg_loss: Decimal = Field(description="Average loss per trade (%)")
    avg_holding_days: Decimal = Field(description="Average holding period in days")
    largest_gain: Decimal = Field(description="Largest single trade gain (%)")
    largest_loss: Decimal = Field(description="Largest single trade loss (%)")

    # Profit factor
    profit_factor: Optional[Decimal] = Field(
        default=None,
        description="Ratio of gross profit to gross loss",
    )

    # Exposure
    avg_num_positions: Decimal = Field(
        description="Average number of positions held"
    )
    max_num_positions: int = Field(description="Maximum positions held simultaneously")

    # Period
    days_traded: int = Field(description="Number of days in backtest period")
    initial_capital: Decimal = Field(description="Initial capital")
    final_capital: Decimal = Field(description="Final capital")


def calculate_metrics(
    snapshots: list[PortfolioSnapshot],
    trades: list[Trade],
    initial_capital: Decimal,
    risk_free_rate: Decimal = Decimal("0.04"),  # 4% annual
) -> PerformanceMetrics:
    """Calculate performance metrics from backtest results.

    Args:
        snapshots: List of portfolio snapshots
        trades: List of completed trades
        initial_capital: Initial capital amount
        risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculation

    Returns:
        Performance metrics
    """
    if not snapshots or not trades:
        # Return empty metrics if no data
        return PerformanceMetrics(
            total_return=Decimal("0"),
            total_return_pct=Decimal("0"),
            cagr=Decimal("0"),
            max_drawdown=Decimal("0"),
            max_drawdown_duration=0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=Decimal("0"),
            avg_gain=Decimal("0"),
            avg_loss=Decimal("0"),
            avg_holding_days=Decimal("0"),
            largest_gain=Decimal("0"),
            largest_loss=Decimal("0"),
            avg_num_positions=Decimal("0"),
            max_num_positions=0,
            days_traded=0,
            initial_capital=initial_capital,
            final_capital=initial_capital,
        )

    # Basic returns
    final_capital = snapshots[-1].total_value
    total_return = final_capital - initial_capital
    total_return_pct = (total_return / initial_capital) * 100

    # CAGR
    days_traded = (snapshots[-1].timestamp - snapshots[0].timestamp).days
    years = days_traded / 365.25
    if years > 0:
        cagr_value = (float(final_capital) / float(initial_capital)) ** (1 / years) - 1
        cagr = Decimal(str(cagr_value * 100))
    else:
        cagr = Decimal("0")

    # Drawdown calculation
    equity_curve = [float(s.total_value) for s in snapshots]
    max_dd, max_dd_duration = _calculate_max_drawdown(equity_curve)

    # Daily returns for Sharpe/Sortino
    daily_returns = np.diff(equity_curve) / equity_curve[:-1]
    sharpe = _calculate_sharpe_ratio(daily_returns, float(risk_free_rate))
    sortino = _calculate_sortino_ratio(daily_returns, float(risk_free_rate))

    # Trade statistics
    winning_trades = [t for t in trades if t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl < 0]

    total_trades = len(trades)
    num_wins = len(winning_trades)
    num_losses = len(losing_trades)
    win_rate = (num_wins / total_trades * 100) if total_trades > 0 else Decimal("0")

    # Average gains/losses
    avg_gain = (
        Decimal(str(sum(t.pnl_pct for t in winning_trades) / num_wins))
        if num_wins > 0
        else Decimal("0")
    )
    avg_loss = (
        Decimal(str(sum(t.pnl_pct for t in losing_trades) / num_losses))
        if num_losses > 0
        else Decimal("0")
    )

    # Largest gain/loss
    largest_gain = max((t.pnl_pct for t in trades), default=Decimal("0"))
    largest_loss = min((t.pnl_pct for t in trades), default=Decimal("0"))

    # Average holding days
    avg_holding_days = (
        sum(t.holding_days for t in trades) / total_trades
        if total_trades > 0
        else Decimal("0")
    )

    # Profit factor
    gross_profit = sum(t.pnl for t in winning_trades)
    gross_loss = abs(sum(t.pnl for t in losing_trades))
    profit_factor = (
        Decimal(str(gross_profit / gross_loss)) if gross_loss > 0 else None
    )

    # Position statistics
    num_positions = [s.num_positions for s in snapshots]
    avg_num_positions = Decimal(str(np.mean(num_positions)))
    max_num_positions = max(num_positions)

    return PerformanceMetrics(
        total_return=total_return,
        total_return_pct=total_return_pct,
        cagr=cagr,
        sharpe_ratio=Decimal(str(sharpe)) if sharpe is not None else None,
        sortino_ratio=Decimal(str(sortino)) if sortino is not None else None,
        max_drawdown=Decimal(str(max_dd)),
        max_drawdown_duration=max_dd_duration,
        total_trades=total_trades,
        winning_trades=num_wins,
        losing_trades=num_losses,
        win_rate=Decimal(str(win_rate)),
        avg_gain=avg_gain,
        avg_loss=avg_loss,
        avg_holding_days=Decimal(str(avg_holding_days)),
        largest_gain=largest_gain,
        largest_loss=largest_loss,
        profit_factor=profit_factor,
        avg_num_positions=avg_num_positions,
        max_num_positions=max_num_positions,
        days_traded=days_traded,
        initial_capital=initial_capital,
        final_capital=final_capital,
    )


def _calculate_max_drawdown(equity_curve: list[float]) -> tuple[float, int]:
    """Calculate maximum drawdown and its duration.

    Args:
        equity_curve: List of portfolio values over time

    Returns:
        Tuple of (max_drawdown_pct, max_duration_days)
    """
    peak = equity_curve[0]
    max_dd = 0.0
    max_dd_duration = 0
    current_dd_duration = 0

    for value in equity_curve:
        if value > peak:
            peak = value
            current_dd_duration = 0
        else:
            dd = (peak - value) / peak * 100
            max_dd = max(max_dd, dd)
            current_dd_duration += 1
            max_dd_duration = max(max_dd_duration, current_dd_duration)

    return max_dd, max_dd_duration


def _calculate_sharpe_ratio(
    daily_returns: np.ndarray, risk_free_rate: float
) -> Optional[float]:
    """Calculate Sharpe ratio.

    Args:
        daily_returns: Array of daily returns
        risk_free_rate: Annual risk-free rate

    Returns:
        Sharpe ratio or None if insufficient data
    """
    if len(daily_returns) == 0:
        return None

    daily_rf_rate = risk_free_rate / 252  # 252 trading days per year
    excess_returns = daily_returns - daily_rf_rate

    if np.std(excess_returns) == 0:
        return None

    sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    return float(sharpe)


def _calculate_sortino_ratio(
    daily_returns: np.ndarray, risk_free_rate: float
) -> Optional[float]:
    """Calculate Sortino ratio (uses downside deviation).

    Args:
        daily_returns: Array of daily returns
        risk_free_rate: Annual risk-free rate

    Returns:
        Sortino ratio or None if insufficient data
    """
    if len(daily_returns) == 0:
        return None

    daily_rf_rate = risk_free_rate / 252
    excess_returns = daily_returns - daily_rf_rate

    # Calculate downside deviation (only negative returns)
    downside_returns = excess_returns[excess_returns < 0]
    if len(downside_returns) == 0:
        return None

    downside_std = np.std(downside_returns)
    if downside_std == 0:
        return None

    sortino = np.mean(excess_returns) / downside_std * np.sqrt(252)
    return float(sortino)

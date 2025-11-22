"""Command-line interface for running backtests."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console

from trading_claude.backtest import BacktestEngine
from trading_claude.config import BacktestConfig, StrategyConfig
from trading_claude.data import MarketDataFetcher
from trading_claude.strategy import HighestGainerStrategy

app = typer.Typer(
    name="trading-claude",
    help="A backtesting system for testing trading strategies",
)
console = Console()


@app.command()
def backtest(
    start_date: str = typer.Option(
        "2020-01-01",
        "--start",
        "-s",
        help="Start date (YYYY-MM-DD)",
    ),
    end_date: str = typer.Option(
        "2025-01-01",
        "--end",
        "-e",
        help="End date (YYYY-MM-DD)",
    ),
    initial_capital: float = typer.Option(
        50000.0,
        "--capital",
        "-c",
        help="Initial capital in USD",
    ),
    gain_threshold: float = typer.Option(
        5.0,
        "--gain",
        "-g",
        help="Sell at this gain percentage",
    ),
    max_positions: int = typer.Option(
        10,
        "--max-positions",
        "-p",
        help="Maximum number of positions",
    ),
    stocks_per_day: int = typer.Option(
        1,
        "--stocks-per-day",
        "-n",
        help="Number of stocks to buy per day",
    ),
    lookback_days: int = typer.Option(
        1,
        "--lookback",
        "-l",
        help="Lookback days for gain calculation",
    ),
    stop_loss: Optional[float] = typer.Option(
        None,
        "--stop-loss",
        help="Stop loss percentage (optional)",
    ),
    max_holding_days: Optional[int] = typer.Option(
        None,
        "--max-days",
        help="Maximum holding period in days (optional)",
    ),
    min_price: float = typer.Option(
        5.0,
        "--min-price",
        help="Minimum stock price",
    ),
    cache_dir: str = typer.Option(
        "data/cache",
        "--cache",
        help="Data cache directory",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """Run a backtest with the highest gainer strategy."""
    # Configure logging
    logger.remove()  # Remove default handler
    if verbose:
        logger.add(
            lambda msg: console.print(msg, end=""),
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="DEBUG",
        )
    else:
        logger.add(
            lambda msg: console.print(msg, end=""),
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO",
        )

    # Parse dates
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as e:
        console.print(f"[red]Error parsing dates: {e}[/red]")
        raise typer.Exit(1)

    # Create configurations
    backtest_config = BacktestConfig(
        start_date=start,
        end_date=end,
        initial_capital=Decimal(str(initial_capital)),
        max_positions=max_positions,
        data_cache_dir=Path(cache_dir),
    )

    strategy_config = StrategyConfig(
        gain_threshold_pct=Decimal(str(gain_threshold)),
        stop_loss_pct=Decimal(str(stop_loss)) if stop_loss else None,
        max_holding_days=max_holding_days,
        min_price=Decimal(str(min_price)),
        lookback_days=lookback_days,
        stocks_per_day=stocks_per_day,
    )

    # Initialize components
    console.print("\n[bold blue]🚀 Trading Claude Backtester[/bold blue]\n")
    console.print(f"Strategy: Highest Gainer (sell at {gain_threshold}% gain)")
    console.print(f"Period: {start} to {end}")
    console.print(f"Capital: ${initial_capital:,.2f}\n")

    data_fetcher = MarketDataFetcher(cache_dir=Path(cache_dir))
    strategy = HighestGainerStrategy(strategy_config, data_fetcher)
    
    # Prepare transaction log file
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transaction_log_file = output_dir / f"transactions_{timestamp}.json"
    
    engine = BacktestEngine(strategy, backtest_config, transaction_log_file)

    # Run backtest
    try:
        with console.status("[bold green]Running backtest..."):
            result = engine.run()

        # Print results
        result.print_summary()

        # Save results
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)

        trades_file = output_dir / f"trades_{timestamp}.csv"
        equity_file = output_dir / f"equity_{timestamp}.csv"

        result.get_trades_df().to_csv(trades_file, index=False)
        result.get_equity_curve().to_csv(equity_file, index=False)

        console.print(f"[green]✓[/green] Results saved to:")
        console.print(f"  • {trades_file}")
        console.print(f"  • {equity_file}")
        console.print(f"  • {transaction_log_file}\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Backtest interrupted by user[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"\n[red]Error during backtest: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from trading_claude._version import __version__

    console.print(f"Trading Claude version {__version__}")


if __name__ == "__main__":
    app()

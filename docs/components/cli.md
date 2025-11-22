# CLI Interface Design

## Overview

The CLI (Command-Line Interface) provides the primary way users interact with Trading Claude. It's built using Typer for robust command parsing and Rich for beautiful terminal output.

**Location:** `src/trading_claude/cli.py`

## Design Philosophy

1. **Sensible Defaults** - Works out of the box with minimal configuration
2. **Progressive Disclosure** - Simple usage is simple, complex usage is possible
3. **Beautiful Output** - Use color, formatting, and progress indicators
4. **Non-Interactive** - Suitable for automation and scripting

## Command Structure

```bash
trading-claude [COMMAND] [OPTIONS]
```

### Available Commands

#### `backtest`
Run a trading strategy backtest

**Usage:**
```bash
trading-claude backtest [OPTIONS]
```

**Common Options:**
- `--start`, `-s` - Start date (YYYY-MM-DD)
- `--end`, `-e` - End date (YYYY-MM-DD)
- `--capital`, `-c` - Initial capital (default: $50,000)
- `--gain`, `-g` - Gain threshold % (default: 5.0)
- `--max-positions`, `-p` - Max concurrent positions (default: 10)
- `--stocks-per-day`, `-n` - Stocks to buy per day (default: 1)

**Example:**
```bash
trading-claude backtest \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --capital 10000 \
  --gain 5.0 \
  --max-positions 5
```

#### `version`
Show version information

**Usage:**
```bash
trading-claude version
```

## Entry Point

Configured in `pyproject.toml`:

```toml
[project.scripts]
trading-claude = "trading_claude.cli:app"
```

This creates a `trading-claude` command when installed via pip/pipx/pdm.

## Implementation Details

### Typer Application

```python
app = typer.Typer(
    name="trading-claude",
    help="A backtesting system for testing trading strategies",
)

@app.command()
def backtest(
    start_date: str = typer.Option("2020-01-01", "--start", "-s"),
    end_date: str = typer.Option("2025-01-01", "--end", "-e"),
    # ... more options
):
    """Run a backtest with the highest gainer strategy."""
    # Implementation
```

### Rich Console

**Beautiful Output:**
```python
from rich.console import Console

console = Console()

console.print("\n[bold blue]🚀 Trading Claude Backtester[/bold blue]\n")
console.print(f"Strategy: Highest Gainer (sell at {gain_threshold}% gain)")
```

**Progress Indicators:**
```python
with console.status("[bold green]Running backtest..."):
    result = engine.run()
```

### Output Format

**Console Display:**
```
🚀 Trading Claude Backtester

Strategy: Highest Gainer (sell at 5.0% gain)
Period: 2024-01-01 to 2024-11-22
Capital: $10,000.00

================================================================================
BACKTEST RESULTS SUMMARY
================================================================================

📅 Period: 2024-01-01 to 2024-11-22
💰 Initial Capital: $10,000.00
💰 Final Capital: $12,834.36

📈 RETURNS
  Total Return: $2,834.36 (28.34%)
  CAGR: 32.26%

...

✓ Results saved to:
  • results/trades_20251122_142801.csv
  • results/equity_20251122_142801.csv
  • results/transactions_20251122_142801.json
```

**Files Created:**
- `results/trades_{timestamp}.csv` - All completed trades
- `results/equity_{timestamp}.csv` - Daily portfolio values
- `results/transactions_{timestamp}.json` - Complete transaction log

## Installation Methods

### Method 1: pipx (Recommended for Users)

```bash
# Install from private index
pipx install trading-claude --index-url https://your-private-index/simple

# Use immediately
trading-claude backtest --start 2024-01-01 --end 2024-12-31
```

**Benefits:**
- Isolated environment (no dependency conflicts)
- Global CLI command
- Easy to upgrade/uninstall

### Method 2: pip

```bash
pip install trading-claude --index-url https://your-private-index/simple
```

### Method 3: PDM (For Development)

```bash
# Clone repository
git clone https://github.com/wnmgo/trading-claude
cd trading-claude

# Install dependencies
pdm install

# Run via pdm
pdm run trading-claude backtest --start 2024-01-01
```

### Method 4: Local Install from Source

```bash
# Clone and install
git clone https://github.com/wnmgo/trading-claude
cd trading-claude
pip install -e .

# Use immediately
trading-claude backtest
```

## Configuration

### Default Values

All defaults are in the CLI command definition:

```python
@app.command()
def backtest(
    initial_capital: float = typer.Option(50000.0, "--capital", "-c"),
    gain_threshold: float = typer.Option(5.0, "--gain", "-g"),
    max_positions: int = typer.Option(10, "--max-positions", "-p"),
    # ...
):
```

### Environment Variables

Currently not supported, but could be added:

```python
import os

default_capital = float(os.getenv("TRADING_CLAUDE_CAPITAL", "50000"))
```

## Error Handling

### Invalid Dates

```python
try:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
except ValueError as e:
    console.print(f"[red]Error parsing dates: {e}[/red]")
    raise typer.Exit(1)
```

### Runtime Errors

```python
try:
    result = engine.run()
except KeyboardInterrupt:
    console.print("\n[yellow]Backtest interrupted by user[/yellow]")
    raise typer.Exit(0)
except Exception as e:
    console.print(f"\n[red]Error during backtest: {e}[/red]")
    if verbose:
        raise  # Show full traceback in verbose mode
    raise typer.Exit(1)
```

## Publishing

### Build the Package

```bash
# Ensure version is tagged
git tag v0.1.0
git push --tags

# Build distribution
pdm build
```

This creates:
- `dist/trading_claude-0.1.0-py3-none-any.whl`
- `dist/trading_claude-0.1.0.tar.gz`

### Publish to Private Index

```bash
# Configure private index in pdm config
pdm config repository.private.url https://your-private-index/simple
pdm config repository.private.username your-username
pdm config repository.private.password your-password

# Publish
pdm publish --repository private
```

### Install from Private Index

```bash
pipx install trading-claude \
  --index-url https://your-private-index/simple \
  --pip-args="--trusted-host your-private-index"
```

## Testing CLI

### Manual Testing

```bash
# Test help
trading-claude --help
trading-claude backtest --help

# Test basic run
trading-claude backtest --start 2024-11-01 --end 2024-11-07

# Test with all options
trading-claude backtest \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --capital 10000 \
  --gain 5.0 \
  --max-positions 5 \
  --stocks-per-day 3 \
  --verbose
```

### Automated Testing

```python
from typer.testing import CliRunner
from trading_claude.cli import app

def test_cli_backtest():
    runner = CliRunner()
    result = runner.invoke(app, [
        "backtest",
        "--start", "2024-11-01",
        "--end", "2024-11-07",
        "--capital", "10000"
    ])
    assert result.exit_code == 0
    assert "BACKTEST RESULTS" in result.stdout
```

## Future Enhancements

### 1. Multiple Strategies

```bash
trading-claude backtest --strategy momentum
trading-claude backtest --strategy mean-reversion
```

### 2. Configuration Files

```bash
trading-claude backtest --config my-strategy.yaml
```

### 3. Interactive Mode

```bash
trading-claude interactive
> backtest 2024-01-01 2024-12-31
> analyze trades
> optimize gain-threshold
```

### 4. Comparison Mode

```bash
trading-claude compare \
  --strategy-a highest-gainer \
  --strategy-b mean-reversion \
  --start 2024-01-01 \
  --end 2024-12-31
```

### 5. Live Mode

```bash
trading-claude live --strategy highest-gainer --paper-trading
```

## Summary

The CLI is designed to be:
- **Simple** - One command gets you started
- **Beautiful** - Rich formatting makes output easy to read
- **Flexible** - Many options for customization
- **Standard** - Works with pip, pipx, pdm
- **Scriptable** - Exit codes and output suitable for automation

Users can install once with `pipx install trading-claude` and immediately start backtesting strategies with a single command.

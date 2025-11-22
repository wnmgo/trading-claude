# Installation & Quick Start

## Prerequisites

- Python 3.10 or higher
- pipx (recommended) or pip
- Git (for development install)

## Installation

### Option 1: pipx (Recommended)

pipx installs the CLI tool in an isolated environment:

```bash
pipx install trading-claude --index-url https://your-private-index/simple
```

Verify installation:

```bash
trading-claude --help
```

### Option 2: pip

```bash
pip install trading-claude --index-url https://your-private-index/simple
```

### Option 3: Development Install

```bash
# Clone the repository
git clone https://github.com/wnmgo/trading-claude.git
cd trading-claude

# Install with PDM
pdm install

# Run via PDM
pdm run trading-claude --help
```

## Quick Start

### Run Your First Backtest

```bash
trading-claude backtest \
  --start 2024-01-01 \
  --end 2024-11-22 \
  --capital 10000 \
  --gain 5.0
```

This will:
1. Fetch S&P 500 stock data for 2024
2. Simulate buying highest daily gainers
3. Sell when stocks hit 5% gain
4. Display performance results
5. Save detailed logs to `results/` directory

### View Results

The backtest creates three files in `results/`:

```bash
results/
├── trades_20241122_143000.csv          # All completed trades
├── equity_20241122_143000.csv          # Daily portfolio values
└── transactions_20241122_143000.json   # Complete transaction log
```

### Visualize Transactions

Open the web viewer:

```bash
# Start a local server (or use any HTTP server)
python -m http.server 8000

# Open in browser
open http://localhost:8000/examples/transaction_viewer.html

# Load the JSON file from results/
```

### Analyze Results

Use the analysis script:

```bash
python examples/analyze_transactions.py results/transactions_20241122_143000.json
```

## Configuration

### Command Options

All configuration is via CLI flags:

```bash
trading-claude backtest \
  --start 2024-01-01              # Start date (YYYY-MM-DD)
  --end 2024-12-31                # End date (YYYY-MM-DD)
  --capital 10000                 # Initial capital ($)
  --gain 5.0                      # Sell at 5% gain
  --max-positions 5               # Max concurrent positions
  --stocks-per-day 3              # Buy up to 3 stocks/day
  --lookback 1                    # Days to look back for gains
  --min-price 5.0                 # Minimum stock price ($)
  --cache data/cache              # Cache directory
  --verbose                       # Show debug logs
```

### Cache Directory

Market data is cached in `data/cache/` by default. To use a different location:

```bash
trading-claude backtest --cache /path/to/cache
```

To clear the cache:

```bash
rm -rf data/cache/*
```

## Common Workflows

### Test a Strategy Parameter

```bash
# Try different gain thresholds
for gain in 3.0 5.0 7.0 10.0; do
  echo "Testing $gain% gain threshold"
  trading-claude backtest \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --gain $gain \
    --capital 10000
done
```

### Compare Time Periods

```bash
# Test same strategy in different years
trading-claude backtest --start 2023-01-01 --end 2023-12-31 --gain 5.0
trading-claude backtest --start 2024-01-01 --end 2024-12-31 --gain 5.0
```

### Verify Strategy Compliance

```bash
# Run backtest
trading-claude backtest --start 2024-01-01 --end 2024-12-31

# Analyze the transaction log
python examples/analyze_transactions.py results/transactions_*.json
```

## Troubleshooting

### Command Not Found

```bash
$ trading-claude --help
command not found: trading-claude
```

**Solution:** Ensure pipx bin directory is in your PATH:

```bash
pipx ensurepath
# Restart your shell
```

### Import Errors

```bash
ModuleNotFoundError: No module named 'yfinance'
```

**Solution:** Reinstall with dependencies:

```bash
pipx reinstall trading-claude
```

### Network Errors

```bash
Failed to fetch S&P 500 tickers from Wikipedia
```

**Solution:** The system uses a fallback ticker list. Check your internet connection or the Wikipedia URL may be blocked. The backtest will continue with the fallback list.

### Permission Errors

```bash
PermissionError: [Errno 13] Permission denied: 'data/cache'
```

**Solution:** Create the cache directory with proper permissions:

```bash
mkdir -p data/cache
chmod 755 data/cache
```

## Next Steps

- Read the [Architecture Overview](../architecture/overview.md)
- Learn about [Strategy Engine](../components/strategy-engine.md)
- Understand [Transaction Logging](../components/transaction-logging.md)
- Explore the [API Reference](../api/README.md)

## Uninstallation

### pipx

```bash
pipx uninstall trading-claude
```

### pip

```bash
pip uninstall trading-claude
```

### Development

```bash
cd trading-claude
pdm remove --self
```

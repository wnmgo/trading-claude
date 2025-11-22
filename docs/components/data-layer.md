# Data Layer Design

## Overview

The Data Layer is responsible for fetching, caching, and providing market data to the backtesting engine. It abstracts away the complexity of external APIs and ensures efficient data access.

## Component: MarketDataFetcher

**Location:** `src/trading_claude/data.py`

**Purpose:** Single point of access for all market data needs

### Responsibilities

1. Fetch historical price data from Yahoo Finance
2. Cache data locally to avoid redundant API calls
3. Provide ticker lists (S&P 500)
4. Calculate daily gains for stock screening
5. Lookup prices at specific dates

### Class Diagram

```python
class MarketDataFetcher:
    """
    Attributes:
        cache_dir: Path to cache directory
    
    Methods:
        get_sp500_tickers() -> list[str]
        get_historical_data(symbol, start, end) -> DataFrame
        get_price_at_date(symbol, date) -> Decimal
        get_daily_gainers(tickers, date, lookback) -> DataFrame
        get_stock_info(symbol) -> dict
    """
```

### Design Decisions

#### 1. Caching Strategy

**Decision:** File-based CSV caching

**Implementation:**
```python
cache_file = cache_dir / f"{symbol}_{start_date}_{end_date}.csv"

if cache_file.exists():
    df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
    return df

# Fetch from API
df = ticker.history(start=start_date, end=end_date)
df.to_csv(cache_file)  # Cache for next time
```

**Rationale:**
- **Pro:** Simple, no database dependency
- **Pro:** Human-readable cache files
- **Pro:** Easy to debug (inspect CSV files)
- **Pro:** Fast enough for typical use (35 stocks, 1 year)
- **Con:** Slower than in-memory or database
- **Con:** Not suitable for thousands of stocks

**Alternatives Considered:**

| Alternative | Pros | Cons | Decision |
|------------|------|------|----------|
| SQLite | Faster queries, ACID | Requires schema, migration complexity | Rejected - overkill |
| Parquet | Columnar, compressed | Binary format, extra dependency | Rejected - CSV simpler |
| Redis | Very fast, TTL support | External service, more complex | Rejected - too complex |
| No caching | Always fresh | Slow, API rate limits | Rejected - unusable |

#### 2. Date Timezone Handling

**Problem:** yfinance returns timezone-aware datetimes, causing comparison errors

**Solution:**
```python
def get_price_at_date(self, symbol: str, date: datetime) -> Optional[Decimal]:
    df = self.get_historical_data(symbol, start_date, end_date)
    
    # Strip timezone for consistent comparisons
    df.index = pd.to_datetime(df.index)
    if hasattr(df.index, 'tz') and getattr(df.index, 'tz') is not None:
        df.index = df.index.tz_localize(None)
    df.index = df.index.normalize()
    
    target_date = pd.Timestamp(date).normalize()
    df_filtered = df[df.index <= target_date]
    
    return Decimal(str(df_filtered.iloc[-1]["Close"]))
```

**Rationale:**
- Normalize both target date and index to remove time component
- Strip timezone to enable comparison
- Use `<=` to get closest earlier date (handles weekends/holidays)

#### 3. S&P 500 Ticker List

**Primary Source:** Wikipedia table scraping

**Fallback:** Hardcoded list of 35 major stocks

**Implementation:**
```python
def get_sp500_tickers(self) -> list[str]:
    try:
        # Attempt to fetch from Wikipedia
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        tables = pd.read_html(StringIO(response.text))
        return tables[0]['Symbol'].tolist()
    except Exception as e:
        logger.warning(f"Failed to fetch S&P 500 tickers: {e}")
        # Fallback to hardcoded list
        return ["AAPL", "MSFT", "GOOGL", ...]  # 35 tickers
```

**Rationale:**
- Wikipedia is free and updated regularly
- User-Agent header required to avoid 403 errors
- Fallback ensures system always works
- 35 stocks sufficient for strategy validation

### API Reference

#### `get_historical_data(symbol, start_date, end_date, use_cache=True)`

Fetches OHLCV data for a symbol.

**Parameters:**
- `symbol` (str): Stock ticker (e.g., "AAPL")
- `start_date` (datetime): Start of date range
- `end_date` (datetime): End of date range  
- `use_cache` (bool): Whether to use cached data

**Returns:**
- `pd.DataFrame` with index=Date, columns=[Open, High, Low, Close, Volume]
- `None` if fetch fails

**Side Effects:**
- Writes to cache directory if `use_cache=True`
- Network request if not cached

**Example:**
```python
fetcher = MarketDataFetcher(cache_dir=Path("data/cache"))
df = fetcher.get_historical_data(
    "AAPL",
    datetime(2024, 1, 1),
    datetime(2024, 12, 31)
)
# df contains all trading days in 2024 for AAPL
```

#### `get_price_at_date(symbol, date)`

Gets closing price for a symbol on a specific date.

**Parameters:**
- `symbol` (str): Stock ticker
- `date` (datetime): Target date

**Returns:**
- `Decimal`: Closing price
- `None` if no data available

**Behavior:**
- If exact date not found (weekend/holiday), returns closest earlier date
- Fetches data with 7-day buffer before/after target

**Example:**
```python
price = fetcher.get_price_at_date("TSLA", datetime(2024, 11, 15))
# Returns Decimal("350.25") or None
```

#### `get_daily_gainers(tickers, date, lookback_days=1)`

Calculates percentage gains for multiple stocks.

**Parameters:**
- `tickers` (list[str]): List of stock symbols
- `date` (datetime): Date to calculate gains for
- `lookback_days` (int): Number of days to look back

**Returns:**
- `pd.DataFrame` with columns=[symbol, gain_pct], sorted by gain descending

**Example:**
```python
gainers = fetcher.get_daily_gainers(
    ["AAPL", "MSFT", "TSLA"],
    datetime(2024, 11, 20),
    lookback_days=1
)
# Returns:
#   symbol  gain_pct
#   TSLA    5.2
#   AAPL    1.3
#   MSFT   -0.5
```

### Performance Characteristics

**Caching Impact:**
```
First run (no cache):  ~45s for 35 stocks, 1 year
Second run (cached):   ~2s for same data
```

**Memory Usage:**
- ~50 KB per stock-year of data
- Entire backtest (35 stocks, 1 year): ~2 MB in memory

**Network:**
- ~1 request per stock if not cached
- Rate limit: Yahoo Finance allows ~2000 requests/hour
- Our usage: ~35 requests max (well within limits)

### Error Handling

**Network Errors:**
```python
try:
    df = ticker.history(...)
except Exception as e:
    logger.error(f"Failed to fetch data for {symbol}: {e}")
    return None  # Caller handles None gracefully
```

**Missing Data:**
- Returns empty DataFrame
- Logged as warning
- Strategy skips that stock for that day

**Invalid Cache:**
- Caught during CSV read
- Logged as warning
- Refetches from API

### Testing Strategy

**Unit Tests:**
```python
def test_caching():
    """Verify cache is used on second call"""
    fetcher = MarketDataFetcher(tmp_cache_dir)
    
    # First call - should fetch
    df1 = fetcher.get_historical_data("AAPL", start, end)
    assert cache_file.exists()
    
    # Second call - should use cache (no network)
    df2 = fetcher.get_historical_data("AAPL", start, end)
    pd.testing.assert_frame_equal(df1, df2)
```

**Integration Tests:**
```python
def test_price_lookup():
    """Verify price lookup handles weekends"""
    fetcher = MarketDataFetcher(cache_dir)
    
    # Saturday - should return Friday's price
    price = fetcher.get_price_at_date("AAPL", datetime(2024, 11, 16))  # Saturday
    assert price is not None
    assert price > 0
```

### Future Improvements

#### 1. Multiple Data Sources

**Current:** yfinance only  
**Proposed:** Support Alpha Vantage, Polygon.io, etc.

```python
class MarketDataFetcher:
    def __init__(self, provider="yfinance", **kwargs):
        self.provider = self._create_provider(provider, **kwargs)
    
    def _create_provider(self, name, **kwargs):
        if name == "yfinance":
            return YFinanceProvider(**kwargs)
        elif name == "alphavantage":
            return AlphaVantageProvider(**kwargs)
        # ...
```

**Benefits:**
- Backup when one source fails
- Better data quality options
- International market support

#### 2. Incremental Cache Updates

**Current:** Cache entire date range  
**Proposed:** Update only new dates

```python
def get_historical_data(self, symbol, start, end):
    cached_data = self._load_cache(symbol)
    
    if cached_data is not None:
        # Only fetch dates not in cache
        last_cached_date = cached_data.index.max()
        if end > last_cached_date:
            new_data = self._fetch(symbol, last_cached_date + 1day, end)
            combined = pd.concat([cached_data, new_data])
            self._save_cache(symbol, combined)
            return combined
    
    return self._fetch(symbol, start, end)
```

**Benefits:**
- Faster updates for live data
- Less network usage
- Always fresh data

#### 3. Data Quality Checks

**Proposed:** Validate fetched data

```python
def _validate_data(self, df: pd.DataFrame) -> bool:
    """Check for data quality issues"""
    # Check for gaps
    if df.index.to_series().diff().max() > pd.Timedelta(days=10):
        logger.warning("Large gap in data detected")
        return False
    
    # Check for zero prices
    if (df['Close'] == 0).any():
        logger.error("Zero prices found")
        return False
    
    # Check for outliers (>50% single-day move)
    pct_change = df['Close'].pct_change()
    if pct_change.abs().max() > 0.5:
        logger.warning("Extreme price movement detected")
    
    return True
```

**Benefits:**
- Detect API issues early
- Prevent corrupted backtests
- Better error messages

#### 4. Parallel Fetching

**Current:** Sequential fetching  
**Proposed:** Concurrent requests

```python
from concurrent.futures import ThreadPoolExecutor

def fetch_multiple(self, symbols, start, end):
    """Fetch data for multiple symbols in parallel"""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(self.get_historical_data, sym, start, end): sym
            for sym in symbols
        }
        results = {}
        for future in as_completed(futures):
            symbol = futures[future]
            results[symbol] = future.result()
    return results
```

**Benefits:**
- 5-10x faster for multiple stocks
- Better user experience
- Maxes out API rate limits

### Configuration

**Cache Directory:**
```python
# Default: data/cache
# Override via CLI: --cache data/my_cache
# Or programmatically:
fetcher = MarketDataFetcher(cache_dir=Path("/custom/cache"))
```

**Cache Invalidation:**
- Manually: Delete CSV files
- Programmatically: `use_cache=False` parameter
- Auto: Files older than N days (future feature)

### Dependencies

```toml
[project.dependencies]
yfinance = ">=0.2.66"
pandas = ">=2.0.0"
requests = ">=2.31.0"
lxml = ">=6.0.2"  # For HTML parsing
html5lib = ">=1.1"  # For HTML parsing
```

## Summary

The Data Layer provides a **simple, reliable, and performant** interface to market data through:

1. **Abstraction:** Single API regardless of data source
2. **Caching:** File-based caching for speed and offline use
3. **Robustness:** Fallbacks and error handling
4. **Flexibility:** Easy to extend with new providers

The design prioritizes **simplicity and debuggability** over maximum performance, making it ideal for backtesting use cases where historical data is relatively stable.

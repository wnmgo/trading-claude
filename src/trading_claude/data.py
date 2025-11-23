"""Data fetching and management using yfinance."""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf
from loguru import logger


class MarketDataFetcher:
    """Fetches and caches market data."""

    def __init__(self, cache_dir: Path = Path("data/cache")):
        """Initialize the data fetcher.

        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._data_cache: dict[str, pd.DataFrame] = {}  # In-memory cache

    def get_sp500_tickers(self) -> list[str]:
        """Get list of S&P 500 stock tickers.

        Returns:
            List of ticker symbols
        """
        logger.info("Fetching S&P 500 ticker list")
        try:
            # Read from Wikipedia with headers to avoid 403
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            tables = pd.read_html(url, storage_options={'headers': headers})
            sp500_table = tables[0]
            tickers = sp500_table["Symbol"].tolist()
            
            # Clean tickers (replace dots with dashes for Yahoo Finance)
            tickers = [ticker.replace(".", "-") for ticker in tickers]
            
            logger.info(f"Found {len(tickers)} S&P 500 tickers")
            return tickers
        except Exception as e:
            logger.warning(f"Failed to fetch S&P 500 tickers from Wikipedia: {e}")
            logger.info("Using fallback list of top stocks")
            # Return a larger fallback list
            return [
                # Tech
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
                # Finance
                "JPM", "V", "MA", "BAC", "WFC", "GS", "MS",
                # Healthcare
                "JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "ABT",
                # Consumer
                "WMT", "PG", "KO", "PEP", "COST", "HD", "MCD",
                # Industrial
                "BA", "CAT", "GE", "HON", "UPS", "LMT", "MMM",
            ]

    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        use_cache: bool = True,
    ) -> Optional[pd.DataFrame]:
        """Get historical OHLCV data for a symbol.

        Args:
            symbol: Stock ticker symbol
            start_date: Start date for data
            end_date: End date for data
            use_cache: Whether to use cached data

        Returns:
            DataFrame with OHLCV data, or None if failed
        """
        # Check in-memory cache first
        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        # Check file cache
        cache_file = self.cache_dir / f"{cache_key}.csv"
        if use_cache and cache_file.exists():
            logger.debug(f"Loaded {symbol} data from cache")
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            self._data_cache[cache_key] = df  # Store in memory
            return df
        
        # Fetch from yfinance
        try:
            logger.debug(f"Fetching {symbol} data from Yahoo Finance")
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                auto_adjust=True,
                actions=False,
            )
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Remove timezone from index
            if hasattr(df.index, 'tz') and getattr(df.index, 'tz') is not None:
                df.index = df.index.tz_localize(None)  # type: ignore
            
            # Save to cache
            if use_cache:
                df.to_csv(cache_file)
                logger.debug(f"Cached {symbol} data")
            
            # Store in memory
            self._data_cache[cache_key] = df
            return df
        
        except Exception as e:
            logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None

    def get_stock_info(self, symbol: str) -> dict:
        """Get stock information including market cap, sector, etc.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with stock info
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "symbol": symbol,
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "avg_volume": info.get("averageVolume"),
                "beta": info.get("beta"),
            }
        except Exception as e:
            logger.warning(f"Failed to fetch info for {symbol}: {e}")
            return {"symbol": symbol}

    def preload_data(
        self,
        tickers: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """Preload all ticker data for the backtest period.
        
        Args:
            tickers: List of ticker symbols to preload
            start_date: Start date for data
            end_date: End date for data
        """
        logger.info(f"Preloading data for {len(tickers)} tickers...")
        for ticker in tickers:
            self.get_historical_data(ticker, start_date, end_date)
        logger.info("Data preload complete")

    def get_daily_gainers(
        self,
        tickers: list[str],
        date: datetime,
        lookback_days: int = 1,
    ) -> pd.DataFrame:
        """Get stocks sorted by daily gain percentage.

        Args:
            tickers: List of ticker symbols to check
            date: Date to calculate gains for
            lookback_days: Number of days to look back

        Returns:
            DataFrame with tickers and their gains, sorted descending
        """
        gains = []
        start_date = date - timedelta(days=lookback_days + 5)  # Extra buffer

        for ticker in tickers:
            try:
                df = self.get_historical_data(ticker, start_date, date)
                if df is None or len(df) < lookback_days + 1:
                    continue

                # Get the prices
                current_price = df.iloc[-1]["Close"]
                previous_price = df.iloc[-(lookback_days + 1)]["Close"]

                if previous_price > 0:
                    gain_pct = ((current_price - previous_price) / previous_price) * 100
                    volume = df.iloc[-1]["Volume"]

                    gains.append(
                        {
                            "symbol": ticker,
                            "gain_pct": float(gain_pct),
                            "price": float(current_price),
                            "volume": int(volume),
                        }
                    )
            except Exception as e:
                logger.debug(f"Error processing {ticker}: {e}")
                continue

        if not gains:
            return pd.DataFrame()

        df = pd.DataFrame(gains)
        df = df.sort_values("gain_pct", ascending=False)
        return df

    def get_price_at_date(
        self,
        symbol: str,
        date: datetime,
        price_type: str = "Close",
    ) -> Optional[Decimal]:
        """Get price for a symbol at a specific date.

        Args:
            symbol: Stock ticker symbol
            date: Date to get price for
            price_type: Type of price to get ("Close" or "Open")

        Returns:
            Price as Decimal, or None if not available
        """
        start_date = date - timedelta(days=7)  # Buffer for weekends/holidays
        end_date = date + timedelta(days=1)

        df = self.get_historical_data(symbol, start_date, end_date)
        if df is None or df.empty:
            return None

        try:
            # Convert date to pandas Timestamp (no timezone)
            target_date = pd.Timestamp(date).normalize()
            
            # Convert index to datetime and remove timezone/normalize
            df.index = pd.to_datetime(df.index)
            if hasattr(df.index, 'tz') and getattr(df.index, 'tz') is not None:
                df.index = df.index.tz_localize(None)  # type: ignore
            df.index = df.index.normalize()  # type: ignore
            
            # Get the price for the exact date or the closest earlier date  
            df_filtered = df[df.index <= target_date]
            if df_filtered.empty:
                return None
            price = df_filtered.iloc[-1][price_type]
            return Decimal(str(price))
        except Exception as e:
            logger.error(f"Error getting {price_type} price for {symbol} at {date}: {e}")
            return None

    def get_open_price(
        self,
        symbol: str,
        date: datetime,
    ) -> Optional[Decimal]:
        """Get opening price for a symbol at a specific date.

        Args:
            symbol: Stock ticker symbol
            date: Date to get opening price for

        Returns:
            Opening price as Decimal, or None if not available
        """
        return self.get_price_at_date(symbol, date, price_type="Open")

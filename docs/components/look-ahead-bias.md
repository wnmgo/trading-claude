# Look-Ahead Bias - FIXED ✅

## Status: **ELIMINATED**

As of the latest version, the look-ahead bias has been fixed using **next-day open execution**.

---

## What Was the Problem?

The original implementation had a **look-ahead bias** that gave unrealistic results.

### Original Flow (WRONG)

```text
Day 1 @ 4:00 PM:
  1. Market closes at $195.78 (AAPL up 6.19%)
  2. Strategy detects AAPL as highest gainer using closing price
  3. Buy order executes at closing price $195.78
  
# This is impossible in real trading!
```

### Why It Was Unrealistic

**You cannot execute at the closing price if you're using that closing price to make the decision.**

In real trading:
- Closing prices are only known AFTER market close (4:00 PM)
- By the time you analyze the data, the market is closed
- Your next opportunity to trade is tomorrow's open (9:30 AM)
- Tomorrow's open price may be very different from today's close

---

## The Solution Implemented

**Next-Day Open Execution** eliminates the bias completely.

### New Flow (CORRECT)

```text
Day 1 @ 4:00 PM:
  1. Market closes, AAPL up 6.19% at $195.78
  2. Strategy detects AAPL as highest gainer
  3. Signal is QUEUED for tomorrow
  
Day 2 @ 9:30 AM:
  4. Market opens at $197.50 (gap up!)
  5. Buy order executes at OPEN price $197.50
  
# This matches real trading!
```

### Code Implementation

The backtest engine now uses a **pending signals queue**:

```python
# In BacktestEngine.__init__:
self.pending_signals: list[tuple[str, int, datetime]] = []

# In daily loop:
while current_date <= end_date:
    # Step 1: Execute YESTERDAY's signals at TODAY's OPEN
    if self.pending_signals:
        for symbol, shares, signal_date in self.pending_signals:
            open_price = data_fetcher.get_open_price(symbol, current_date)
            portfolio.buy(symbol, shares, open_price, current_date)
        self.pending_signals = []
    
    # Step 2: Update positions, check sells
    # ...
    
    # Step 3: Generate NEW signals for TOMORROW
    buy_signals = strategy.generate_signals(current_date, ...)
    for symbol, shares in buy_signals:
        self.pending_signals.append((symbol, shares, current_date))
```

### Key Changes

1. **Added `get_open_price()` method** to `MarketDataFetcher`
   - Fetches opening price instead of closing price
   - Uses same caching mechanism as closing prices

2. **Added `pending_signals` queue** to `BacktestEngine`
   - Stores signals from previous day
   - Tracks: (symbol, shares, signal_date)

3. **Reordered execution steps**:
   - **Old:** Update → Sell → Generate signals → Execute signals (same day)
   - **New:** Execute pending → Update → Sell → Generate signals for tomorrow

4. **Transaction logging updated**:
   - Signal events include `execution_date` metadata
   - Buy reason now says "will execute at next day's open"

---

## Impact on Results

### Expected Changes After Fix

After eliminating the bias, you should see:

**Lower Returns (More Realistic)**
- Original with bias: Entered at optimal momentum close
- Fixed version: Enters next day, may gap up or down
- Estimated impact: -2% to -5% annual return

**Higher Volatility**
- Capturing overnight gaps (both positive and negative)
- More realistic price slippage
- Better reflects real market conditions

**Different Trade Characteristics**
- Entry prices higher on average (gap-ups after momentum days)
- Some signals may not execute (if stock gaps down too much)
- More accurate representation of strategy performance

### Verification

You can verify the fix by checking transaction logs:

```python
# All buy orders should execute next day
for event in transaction_log:
    if event["event_type"] == "signal" and event["signal_type"] == "buy":
        signal_date = event["timestamp"]
        execution_date = event["metadata"]["execution_date"]
        
        # These should be DIFFERENT days
        assert execution_date > signal_date
        assert (execution_date - signal_date).days >= 1
```

---

## Share Calculation

**All share calculations use `int()` to ensure whole shares only.**

### In Strategy Signal Generation

```python
# strategy.py line 152
cash_per_stock = cash_available / stocks_to_buy
shares = int(cash_per_stock / price)  # Always whole number
```

### In Portfolio Position Sizing

```python
# backtest.py line 96
max_position_value = total_value * (max_position_size_pct / 100)
shares = int(max_position_value / execution_price)  # Adjusted to whole shares
```

**No partial shares are ever purchased.** The `int()` function truncates fractional shares, so if the calculation yields 10.8 shares, only 10 are purchased.

---

## Comparison: Original vs Fixed

| Aspect | Original (Biased) | Fixed (Realistic) |
|--------|------------------|-------------------|
| **Signal** | Day 1 close | Day 1 close |
| **Execution** | Day 1 close | Day 2 open |
| **Price** | $195.78 | $197.50 (gap up) |
| **Bias** | Yes - look-ahead | No - realistic |
| **Entry** | Perfect timing | Real-world delay |
| **Returns** | Inflated | Accurate |
| **Gaps** | Ignored | Captured |

### Example Trade Comparison

```text
Original (Look-Ahead Bias):
  Nov 4 @ close: Signal + Execute at $195.78
  Nov 6 @ close: Sell at $207.09
  Return: +5.78%
  
Fixed (No Bias):
  Nov 4 @ close: Signal at $195.78
  Nov 5 @ open: Execute at $197.50 (gap up)
  Nov 6 @ close: Sell at $207.09
  Return: +4.86%
  
Difference: -0.92% due to overnight gap
```

---

## Why Next-Day Open (Not Next-Day Close)?

We chose **next-day open** over next-day close because:

**Pros:**
- ✅ **Most realistic:** Matches how algorithmic trading actually works
- ✅ **Market hours execution:** Can't trade when market is closed
- ✅ **Captures gaps:** Reflects true overnight price movements
- ✅ **Standard practice:** Industry-standard backtesting approach

**Considered but rejected: Next-Day Close**
- ❌ Still unrealistic (waiting full day after signal)
- ❌ Misses intraday opportunities
- ❌ Doesn't match real trading behavior

---

## Technical Notes

### Open Price Data Availability

Yahoo Finance provides OHLCV (Open, High, Low, Close, Volume) data:
- ✅ Open prices are available for all dates
- ✅ Same caching mechanism as close prices
- ✅ No additional API calls needed (already in cached data)

### Edge Cases Handled

1. **No open price available:**
   - Order is not executed
   - Warning logged
   - Signal discarded

2. **Weekend/holiday signals:**
   - Signals queue until next trading day
   - Execute at next available open

3. **End of backtest period:**
   - Pending signals at final day are not executed
   - Logged for transparency

---

## Summary

**Before:** Signal and execute same day using same price = Look-ahead bias ⚠️

**After:** Signal on Day N, execute on Day N+1 at open = No look-ahead bias ✅

This fix ensures backtest results are **realistic and actionable** for real trading.

### Why It's Unrealistic

**You cannot execute at the closing price if you're using that closing price to make the decision.**

In real trading:
- Closing prices are only known AFTER market close (4:00 PM)
- By the time you analyze the data, the market is closed
- Your next opportunity to trade is tomorrow's open (9:30 AM)
- Tomorrow's open price may be very different from today's close

### Example of the Bias

```
Current Backtest (Look-Ahead):
  Day 1: See AAPL closed +6.19% at $195.78
  Day 1: Buy at $195.78 (closing price)
  Day 2: AAPL opens at $197.50 (+0.88%)
  Day 3: Sell at $206.88 (+5.67% from entry)
  
  Result: Profit based on $195.78 entry

Realistic Backtest (No Look-Ahead):
  Day 1: See AAPL closed +6.19% at $195.78
  Day 2: Buy at OPEN $197.50 (next day)
  Day 3: Sell at $206.88 (+4.75% from entry)
  
  Result: Lower profit due to gap-up entry
```

### Impact on Results

The look-ahead bias **inflates returns** because:

1. **Best entry prices:** You're buying at the close of a momentum day
2. **Missing gaps:** You avoid overnight gaps that occur before you can execute
3. **Perfect timing:** You get the exact price you used to make the decision

**Your 28.34% return might be overstated!**

### The Fix

Two approaches to eliminate the bias:

#### Option 1: Next-Day Execution (Most Realistic)

```python
# Day loop changes:
while current_date <= end_date:
    # 1. Execute YESTERDAY's signals at today's OPEN
    if pending_signals:
        for symbol, shares in pending_signals:
            open_price = get_open_price(symbol, current_date)
            portfolio.buy(symbol, shares, open_price, current_date)
        pending_signals = []
    
    # 2. Check sells at today's prices
    for position in positions:
        if should_sell(position, current_date):
            portfolio.sell(position.symbol, current_date)
    
    # 3. Generate NEW signals for tomorrow
    pending_signals = strategy.generate_signals(current_date, ...)
    
    current_date += timedelta(days=1)
```

**Pros:**
- Most realistic
- Matches real trading
- Shows true strategy performance

**Cons:**
- Need to fetch open prices (may not be in yfinance data)
- More complex code
- Lower returns (realistic ones!)

#### Option 2: Next-Day Close Execution (Simpler)

```python
# Day loop changes:
while current_date <= end_date:
    # 1. Execute YESTERDAY's signals at today's CLOSE
    if pending_signals:
        for symbol, shares in pending_signals:
            close_price = get_price_at_date(symbol, current_date)
            portfolio.buy(symbol, shares, close_price, current_date)
        pending_signals = []
    
    # 2. Check sells, generate signals
    # 3. Store signals for tomorrow
    pending_signals = strategy.generate_signals(current_date, ...)
```

**Pros:**
- Uses existing close prices (no new data needed)
- Still eliminates look-ahead bias
- Simpler than Option 1

**Cons:**
- Less realistic than open execution
- Assumes you can trade at close next day

### Recommended Solution

**Use Option 2 (Next-Day Close)** for now because:
- ✅ Eliminates the bias
- ✅ No new data requirements
- ✅ Minimal code changes
- ✅ Still more realistic than current

Later, upgrade to Option 1 if you want maximum realism.

### Code Changes Required

1. **BacktestEngine.run()**: Add signal queue
2. **Strategy.generate_signals()**: Remove price fetching (use yesterday's data)
3. **Transaction logging**: Add "signal_date" vs "execution_date"

### Expected Impact

After fixing, you should see:
- **Lower returns** (more realistic)
- **Higher volatility** (capturing overnight gaps)
- **Different trade entries** (not at ideal momentum closes)

### Verification

To verify the fix works:
```python
# Check transaction log
for trade in trades:
    signal_date = trade.signal_date
    execution_date = trade.execution_date
    
    # These should be DIFFERENT days
    assert execution_date > signal_date
    assert (execution_date - signal_date).days >= 1
```

## Summary

**Current:** Signal and execute on same day using same price = Look-ahead bias ⚠️

**Fixed:** Signal on Day 1, execute on Day 2 = No look-ahead bias ✅

This is a **critical issue** that affects the validity of your backtest results.

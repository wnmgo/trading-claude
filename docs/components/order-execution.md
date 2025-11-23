# Order Execution - Complete Walkthrough

## Order Type: Market Orders (Not Limit Orders)

**Yes, the system executes MARKET ORDERS**, meaning orders execute immediately at the current market price (with slippage). There are no limit orders or order queues.

## ⚠️ Important: Next-Day Execution (Look-Ahead Bias Eliminated)

**Buy signals execute at the NEXT day's OPEN price, not the same day.**

- **Signal generated:** Day 1 at market close (using closing price to identify gainers)
- **Order executed:** Day 2 at market open (realistic trading flow)

This eliminates **look-ahead bias** and matches real-world trading where you can't execute at the same closing price you used to make the decision.

## Full Execution Flow - Step by Step

### Example Scenario

- **Signal Date:** 2024-11-04 (Monday close)
- **Execution Date:** 2024-11-05 (Tuesday open)
- **Symbol:** AMZN
- **Closing Price Mon:** $195.78 (AMZN up 6.19% - highest gainer)
- **Opening Price Tue:** $197.50 (gap up overnight)
- **Current Cash:** $10,000
- **Slippage:** 0.1% (default)
- **Commission:** $0 (default)

---

## DAY 1: BUY SIGNAL GENERATION (Monday 4:00 PM)

### Step 1: Signal Generation
```
Strategy identifies AMZN as highest gainer (+6.19%)
Calculates shares needed: 50 shares at $195.78
```

### Step 2: Price Lookup
```python
# Get current market price from data
price = data_fetcher.get_price_at_date("AMZN", datetime(2024, 11, 4))
# Returns: Decimal("195.77999877929688")  # Closing price
```

### Step 3: Calculate Slippage
```python
# Slippage represents market impact + bid-ask spread
slippage = price * (slippage_pct / 100)
slippage = 195.78 * (0.1 / 100)
slippage = 195.78 * 0.001
slippage = $0.19578

# For BUY: Execution price is HIGHER (you pay more)
execution_price = price + slippage
execution_price = $195.78 + $0.19578
execution_price = $195.97578
```

**Why add slippage for buys?**
- When you buy, you're hitting the ASK price
- Market impact pushes price up
- You pay slightly more than the "market price"

### Step 4: Calculate Total Cost
```python
total_cost = (execution_price * shares) + commission
total_cost = ($195.97578 * 50) + $0
total_cost = $9,798.789 + $0
total_cost = $9,798.789
```

### Step 5: Check Cash Availability
```python
if total_cost > cash:
    # REJECT ORDER - insufficient funds
    return False

# We have $10,000, need $9,798.79 ✓ PASS
```

### Step 6: Check Position Size Limit
```python
# Max position size = 20% of portfolio value (default)
max_position_value = total_value * (max_position_size_pct / 100)
max_position_value = $10,000 * 0.20
max_position_value = $2,000

position_value = execution_price * shares
position_value = $195.97578 * 50
position_value = $9,798.789

if position_value > max_position_value:
    # ADJUST SHARES DOWN
    shares = int(max_position_value / execution_price)
    shares = int($2,000 / $195.97578)
    shares = int(10.20...)
    shares = 10  # Adjusted down!
    
    # Recalculate cost
    total_cost = ($195.97578 * 10) + $0
    total_cost = $1,959.7578
```

**This is why you saw "BUY 10 AMZN" instead of 50!**

### Step 7: Execute Order
```python
# Deduct cash
cash_before = $10,000
cash -= total_cost
cash = $10,000 - $1,959.7578
cash_after = $8,040.24

# Create position
position = Position(
    symbol="AMZN",
    shares=10,
    entry_price=$195.97578,  # This is your cost basis
    entry_date=2024-11-04,
    current_price=$195.97578
)
```

### Step 8: Log Transaction
```json
{
  "event_type": "order",
  "order_type": "BUY",
  "symbol": "AMZN",
  "shares": 10,
  "target_price": "195.77999877929688",    // Market price
  "actual_price": "195.97577877807617688", // Execution price (with slippage)
  "slippage": "0.19577999877929688",       // $0.196
  "commission": "0",
  "total_cost": "1959.75778778076176880",  // $1,959.76
  "cash_before": "10000.0",
  "cash_after": "8040.24221221923823120"
}
```

---

## SELL ORDER EXECUTION

### Example: 2 Days Later (2024-11-06)

### Step 1: Price Update
```python
# Each day, update all position prices
current_price = get_price_at_date("AMZN", datetime(2024, 11, 6))
current_price = $207.09

position.current_price = $207.09
position.unrealized_pnl_pct = ((207.09 - 195.97578) / 195.97578) * 100
position.unrealized_pnl_pct = 5.67%
```

### Step 2: Check Sell Signal
```python
# Strategy checks: Has gain hit threshold?
if position.unrealized_pnl_pct >= gain_threshold_pct:
    # 5.67% >= 5.0% ✓ SELL SIGNAL
    should_sell = True
```

### Step 3: Calculate Slippage
```python
sell_price = $207.09  # Current market price

# For SELL: Slippage is SUBTRACTED (you receive less)
slippage = sell_price * (slippage_pct / 100)
slippage = $207.09 * 0.001
slippage = $0.20709

execution_price = sell_price - slippage
execution_price = $207.09 - $0.20709
execution_price = $206.88291
```

**Why subtract slippage for sells?**
- When you sell, you're hitting the BID price
- Market impact pushes price down
- You receive slightly less than the "market price"

### Step 4: Calculate Proceeds
```python
gross_proceeds = execution_price * shares
gross_proceeds = $206.88291 * 10
gross_proceeds = $2,068.8291

net_proceeds = gross_proceeds - commission
net_proceeds = $2,068.8291 - $0
net_proceeds = $2,068.8291
```

### Step 5: Execute Sell
```python
# Add to cash
cash_before = $8,040.24
cash += net_proceeds
cash = $8,040.24 + $2,068.83
cash_after = $10,109.07

# Calculate P&L
cost_basis = entry_price * shares
cost_basis = $195.97578 * 10
cost_basis = $1,959.7578

pnl = net_proceeds - cost_basis
pnl = $2,068.8291 - $1,959.7578
pnl = $109.07

pnl_pct = (pnl / cost_basis) * 100
pnl_pct = ($109.07 / $1,959.76) * 100
pnl_pct = 5.67%
```

### Step 6: Log Transaction
```json
{
  "event_type": "order",
  "order_type": "SELL",
  "symbol": "AMZN",
  "shares": 10,
  "target_price": "207.08999633789065",    // Market price
  "actual_price": "206.88290634155275935", // Execution price (minus slippage)
  "slippage": "0.20708999633789065",       // $0.207
  "commission": "0",
  "total_cost": "2068.82906341552759350",  // Proceeds (not cost)
  "cash_before": "8040.24",
  "cash_after": "10109.07"
}
```

### Step 7: Record Completed Trade
```json
{
  "event_type": "trade_completed",
  "symbol": "AMZN",
  "entry_date": "2024-11-04",
  "exit_date": "2024-11-06",
  "entry_price": "195.97577877807617688",
  "exit_price": "206.88290634155275935",
  "shares": 10,
  "pnl": "109.07127563476582470",          // Profit
  "pnl_pct": "5.671219999283820354",       // 5.67% gain
  "holding_days": 2
}
```

### Step 8: Remove Position
```python
# Delete from positions dictionary
del self.positions["AMZN"]
```

---

## Key Differences: Market Orders vs Limit Orders

| Aspect | Market Orders (Current) | Limit Orders (Not Implemented) |
|--------|------------------------|-------------------------------|
| **Execution** | Immediate at current price + slippage | Only if price reaches limit |
| **Guarantee** | Execution guaranteed (if cash available) | Execution not guaranteed |
| **Price** | Variable (market price ± slippage) | Fixed (your limit price) |
| **Complexity** | Simple, instant | Requires order book, matching |
| **Realism** | Good for backtesting | More realistic for live trading |

---

## Slippage Model Details

### What Slippage Represents

1. **Bid-Ask Spread:** Difference between buy and sell prices
2. **Market Impact:** Your order moving the price
3. **Execution Delay:** Price movement during order routing

### Default Configuration
- **Slippage:** 0.1% (10 basis points)
- **Commission:** $0 (many brokers offer commission-free trading now)

### Example Impact on $10,000 Trade

```
Without Slippage:
  Buy:  $10,000.00
  Sell: $10,500.00 (5% gain)
  Profit: $500.00 (5.0%)

With 0.1% Slippage:
  Buy:  $10,010.00  (+$10 slippage)
  Sell: $10,489.50  (-$10.50 slippage)
  Profit: $479.50 (4.78%)
  
Slippage cost: $20.50 (0.2% of trade value)
```

### Configuring Slippage

Users can adjust via configuration:

```python
BacktestConfig(
    slippage_pct=Decimal("0.05"),  # 0.05% = 5 basis points (tight)
    # or
    slippage_pct=Decimal("0.5"),   # 0.5% = 50 basis points (loose)
)
```

---

## Position Sizing Logic

### Scenario 1: Simple Buy (Enough Cash)
```
Signal: Buy 100 shares of AAPL @ $150
Max position size: 20% of $10,000 = $2,000
Position value: 100 * $150 = $15,000

Result: Adjust to 13 shares ($1,950)
```

### Scenario 2: Insufficient Cash
```
Cash: $1,000
Signal: Buy 100 shares @ $150
Total needed: $15,000

Result: Order REJECTED (insufficient funds)
```

### Scenario 3: Averaging In
```
Existing position: 10 shares @ $195.98
New buy: 5 shares @ $200.00

New average price = (10*$195.98 + 5*$200.00) / 15
                  = ($1,959.80 + $1,000.00) / 15
                  = $197.32

New position: 15 shares @ $197.32
```

---

## Order Timing

### When Are Orders Executed?

**Daily Close Prices Only**

The simulation uses **end-of-day (EOD) closing prices**:

```python
# Day loop in backtest engine
for each trading day:
    1. Update all position prices (using closing price)
    2. Check sell signals
    3. Execute sells (at closing price)
    4. Generate buy signals
    5. Execute buys (at closing price)
```

**This means:**
- ✅ Orders execute at market close (like MOC - Market On Close orders)
- ✅ No intraday price movements
- ✅ No execution during market hours
- ❌ Can't capture intraday volatility
- ❌ Can't simulate limit orders during the day

---

## Why Market Orders?

### Advantages for Backtesting

1. **Simplicity:** No order book, no partial fills
2. **Guaranteed Execution:** If cash available, order executes
3. **Realistic:** Most retail trading is market orders
4. **Fast:** No complex matching algorithms
5. **Deterministic:** Same inputs = same results

### Trade-offs

- **Less realistic for large orders:** Real large orders impact market more
- **No limit order strategies:** Can't test "buy the dip" with limits
- **No order queue:** Can't simulate FIFO/priority rules

---

## Summary

### Order Execution is:
✅ **Market Orders** at closing prices  
✅ **Immediate execution** (no queue)  
✅ **Slippage applied** (0.1% default)  
✅ **Position size limits** enforced (20% max)  
✅ **Cash constraints** checked  
✅ **Fully logged** in transaction JSON  

### Not Implemented:
❌ Limit orders  
❌ Stop-loss orders (as separate order type)  
❌ Intraday execution  
❌ Order books or matching engines  
❌ Partial fills  
❌ Order priority/FIFO  

The system is designed for **end-of-day backtesting** with **simple, realistic market orders** that execute immediately at the closing price with configurable slippage.

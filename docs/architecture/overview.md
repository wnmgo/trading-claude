# Architecture Overview

## System Purpose

Trading Claude is a backtesting system designed to validate trading strategies using historical market data. It simulates portfolio management, order execution, and performance tracking to answer the question: **"Would this trading strategy have been profitable?"**

## Bird's Eye View

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  CLI (Typer) │  │ Web Viewer   │  │  Analysis Scripts    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼───────────────────────┼─────────────┘
          │                  │                       │
          ▼                  │                       ▼
┌─────────────────────────────┼─────────────────────────────────────┐
│                Core Engine  │                                      │
│  ┌──────────────────────────▼────────────────────────────┐        │
│  │          Backtest Engine                              │        │
│  │  • Portfolio Management                               │        │
│  │  • Order Execution (with slippage/commission)        │        │
│  │  • Daily Simulation Loop                             │        │
│  │  • Transaction Logging                               │        │
│  └────────┬──────────────────────────────┬───────────────┘        │
│           │                              │                         │
│  ┌────────▼──────────┐        ┌─────────▼─────────┐              │
│  │  Strategy Engine  │        │  Metrics Engine   │              │
│  │  • Signal Gen.    │        │  • CAGR, Sharpe   │              │
│  │  • Exit Rules     │        │  • Drawdown       │              │
│  │  • Position Size  │        │  • Win Rate       │              │
│  └────────┬──────────┘        └───────────────────┘              │
└───────────┼──────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Market Data  │  │    Cache     │  │   Configuration      │  │
│  │  (yfinance)  │  │    (CSV)     │  │    (Pydantic)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Transaction  │  │    Trades    │  │   Equity Curve       │  │
│  │  Logs (JSON) │  │    (CSV)     │  │      (CSV)           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Major Components

### 1. User Interface Layer

**Responsibilities:**
- Accept user inputs (strategy parameters, date ranges, capital)
- Display results (metrics, trades, visualizations)
- Provide multiple interaction modes (CLI, web, programmatic)

**Key Technologies:**
- Typer (CLI framework)
- Rich (terminal formatting)
- HTML/JavaScript (web viewer)

### 2. Core Engine

#### 2.1 Backtest Engine
**Purpose:** Simulates portfolio management and order execution

**Key Features:**
- Day-by-day market simulation
- Realistic order execution (slippage, commissions)
- Position tracking and updates
- Portfolio snapshots
- Transaction logging

**Design Pattern:** Event-driven simulation loop

#### 2.2 Strategy Engine
**Purpose:** Generates trading signals based on market conditions

**Key Features:**
- Pluggable strategy interface
- Market data integration
- Configurable parameters
- Buy/sell signal generation

**Design Pattern:** Strategy pattern (abstract base class)

#### 2.3 Metrics Engine
**Purpose:** Calculates performance statistics

**Key Features:**
- Return calculations (total, CAGR)
- Risk metrics (Sharpe, Sortino, max drawdown)
- Trade statistics (win rate, avg gain/loss)
- Position analytics

**Design Pattern:** Pure functions with immutable inputs

### 3. Data Layer

#### 3.1 Market Data Fetcher
**Purpose:** Retrieve historical stock prices

**Key Features:**
- Yahoo Finance integration (yfinance)
- CSV caching for performance
- S&P 500 ticker list management
- Price lookup by date

**Design Pattern:** Repository pattern with caching

#### 3.2 Configuration
**Purpose:** Validate and manage settings

**Key Features:**
- Type-safe configuration (Pydantic models)
- Validation rules
- Default values
- Serialization support

**Design Pattern:** Pydantic models for data validation

### 4. Storage Layer

#### 4.1 Transaction Logs
**Purpose:** Complete audit trail in machine-parsable format

**Format:** JSON with structured events
- backtest_init, signal, order, trade_completed
- position_update, portfolio_snapshot
- backtest_complete

**Use Cases:**
- Strategy verification
- Programmatic replay
- Human review (via web viewer)

#### 4.2 Results Files
**Purpose:** Export data for analysis

**Formats:**
- Trades CSV: All completed trades
- Equity CSV: Daily portfolio values

## Data Flow

### 1. Initialization Phase
```
User Input → Configuration Validation → Strategy Setup → Data Fetcher Init
```

### 2. Simulation Phase (Daily Loop)
```
For each trading day:
  1. Update position prices (Data Layer)
  2. Check sell signals (Strategy Engine)
  3. Execute sells (Backtest Engine) → Log transaction
  4. Generate buy signals (Strategy Engine)
  5. Execute buys (Backtest Engine) → Log transaction
  6. Take portfolio snapshot → Log snapshot
```

### 3. Analysis Phase
```
Portfolio State → Metrics Calculator → Performance Report
Transaction Log → Compliance Checker → Verification Report
```

### 4. Output Phase
```
Results → CSV Export + JSON Log → File System
Results → CLI Display → User Terminal
Results → Web Viewer → Browser
```

## Key Design Decisions

### 1. Event-Driven Simulation
**Decision:** Simulate each trading day sequentially

**Rationale:**
- Prevents look-ahead bias
- Realistic order execution timing
- Easy to understand and debug
- Matches real trading constraints

**Trade-offs:**
- Slower than vectorized backtesting
- But: More accurate and verifiable

### 2. Immutable Data Models
**Decision:** Use Pydantic with frozen models

**Rationale:**
- Type safety at runtime
- Validation on construction
- Serialization support
- Prevents accidental mutations

**Trade-offs:**
- Requires model copying for updates
- But: Eliminates state bugs

### 3. Comprehensive Transaction Logging
**Decision:** Log every event in structured JSON

**Rationale:**
- Complete audit trail
- Strategy verification
- Debugging support
- Regulatory compliance ready

**Trade-offs:**
- Larger file sizes
- But: Invaluable for verification

### 4. Pluggable Strategy Pattern
**Decision:** Abstract base class for strategies

**Rationale:**
- Easy to add new strategies
- Consistent interface
- Testable in isolation
- Composition over inheritance

**Trade-offs:**
- Slight boilerplate
- But: Clean separation of concerns

### 5. CSV Caching
**Decision:** Cache market data as CSV (not database)

**Rationale:**
- Human-readable
- No dependencies
- Fast enough for typical use
- Easy to inspect/debug

**Trade-offs:**
- Not as fast as database
- But: Simpler deployment

## System Constraints

### Performance
- **Target:** Process 1 year of data for 35 stocks in < 60 seconds
- **Bottleneck:** Market data fetching (mitigated by caching)

### Accuracy
- **Slippage:** 0.1% default (configurable)
- **Commission:** $0 default (configurable)
- **Price:** Using close prices (not intraday)

### Scalability
- **Stocks:** Designed for 10-100 stocks
- **Date Range:** Works with years of data
- **Memory:** Holds all data in memory (acceptable for typical use)

## Error Handling Strategy

### Data Errors
- Missing prices → Skip that day's signals for that stock
- Network failures → Retry with exponential backoff
- Invalid cache → Refetch data

### Configuration Errors
- Invalid dates → Clear error message + exit
- Bad parameters → Validation error with guidance

### Execution Errors
- Insufficient cash → Log warning, skip order
- Position limit → Adjust share count

## Security Considerations

1. **No Authentication:** Local-only tool (no server)
2. **Data Privacy:** Uses public market data only
3. **File System:** Respects user permissions
4. **Dependencies:** Minimal external deps (reduce attack surface)

## Future Extensibility Points

### 1. Strategy Expansion
- Add sentiment analysis strategies
- Support options/futures
- Multi-asset strategies

### 2. Data Sources
- Alternative data providers
- Real-time data support
- International markets

### 3. Analysis Tools
- Monte Carlo simulations
- Walk-forward optimization
- Strategy comparison tools

### 4. Deployment
- Web service API
- Cloud execution
- Scheduled backtests

### 5. Performance
- Parallel strategy execution
- Database caching
- Incremental backtests

## Technology Stack

| Layer | Technology | Justification |
|-------|------------|---------------|
| Language | Python 3.10+ | Rich ecosystem, data science libs |
| CLI | Typer + Rich | Modern, beautiful CLIs |
| Data Validation | Pydantic | Runtime type checking |
| Market Data | yfinance | Free, reliable Yahoo Finance API |
| Data Processing | Pandas + NumPy | Industry standard |
| Math | SciPy | Statistical calculations |
| Logging | Loguru | Better than stdlib logging |
| Testing | pytest | Standard Python testing |
| Package Manager | PDM | Modern, fast, PEP standards |
| Version Control | Git + GitHub | Industry standard |

## Quality Attributes

### Maintainability
- **Score:** High
- **Features:** Type hints, docstrings, clear separation of concerns

### Testability
- **Score:** High
- **Features:** Pure functions, dependency injection, small modules

### Reliability
- **Score:** High
- **Features:** Extensive validation, error handling, transaction logs

### Performance
- **Score:** Medium
- **Features:** Caching, but not optimized for HFT

### Usability
- **Score:** High
- **Features:** Rich CLI, web viewer, clear documentation

## Summary

Trading Claude is architected as a **layered system** with clear separation between:
- **UI Layer:** Multiple interfaces for different users
- **Core Engine:** Strategy execution and simulation
- **Data Layer:** Market data and configuration
- **Storage Layer:** Results and audit trails

The system prioritizes **accuracy, transparency, and extensibility** over raw performance, making it ideal for strategy validation and learning, while maintaining the flexibility to grow into more advanced use cases.

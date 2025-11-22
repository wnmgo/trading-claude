# Trading Claude Documentation

Welcome to the Trading Claude documentation. This directory contains comprehensive technical documentation for the trading strategy backtesting system.

## Documentation Structure

### 1. [Architecture Overview](./architecture/overview.md)
High-level system design, component interactions, and data flow.

### 2. Component Design Documents

#### Core Components
- [Data Layer](./components/data-layer.md) - Market data fetching and caching
- [Strategy Engine](./components/strategy-engine.md) - Trading strategy implementation
- [Backtesting Engine](./components/backtesting-engine.md) - Portfolio simulation
- [Metrics Calculator](./components/metrics.md) - Performance analysis
- [Transaction Logging](./components/transaction-logging.md) - Audit trail system

#### User Interfaces
- [CLI Interface](./components/cli.md) - Command-line interface
- [Web Viewer](./components/web-viewer.md) - Transaction log visualization

#### Supporting Components
- [Configuration](./components/configuration.md) - Settings and parameters
- [Data Models](./components/models.md) - Core data structures

### 3. [API Reference](./api/README.md)
Detailed API documentation for all public interfaces.

### 4. [User Guide](./user-guide/README.md)
How to install, configure, and use Trading Claude.

### 5. [Development Guide](./development/README.md)
Contributing guidelines, testing, and extending the system.

## Quick Links

- **Installation**: See [User Guide - Installation](./user-guide/installation.md)
- **Quick Start**: See [User Guide - Quick Start](./user-guide/quickstart.md)
- **Architecture**: See [Architecture Overview](./architecture/overview.md)
- **Contributing**: See [Development Guide](./development/contributing.md)

## Philosophy

Trading Claude is designed with these principles:

1. **Transparency** - Every transaction is logged and auditable
2. **Simplicity** - Clean APIs and straightforward configuration
3. **Accuracy** - Realistic simulation with slippage and commissions
4. **Extensibility** - Easy to add new strategies and metrics
5. **Reproducibility** - Deterministic results from transaction logs

## Version

This documentation is for Trading Claude v0.1.0.

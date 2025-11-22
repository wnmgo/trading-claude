"""Transaction logging for detailed audit trail and replay."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from trading_claude.models import OrderType


class TransactionEvent(BaseModel):
    """Base class for all transaction events."""

    timestamp: datetime
    event_type: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = self.model_dump()
        # Convert Decimal to string for JSON serialization
        def convert_decimal(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(item) for item in obj]
            elif isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        result = convert_decimal(data)
        return result  # type: ignore


class BacktestInitEvent(TransactionEvent):
    """Backtest initialization event."""
    
    event_type: str = "backtest_init"
    initial_capital: Decimal
    start_date: datetime
    end_date: datetime
    strategy_name: str
    strategy_config: dict[str, Any]
    backtest_config: dict[str, Any]


class MarketDataEvent(TransactionEvent):
    """Market data fetched for a symbol."""
    
    event_type: str = "market_data"
    symbol: str
    date: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class SignalEvent(TransactionEvent):
    """Trading signal generated."""
    
    event_type: str = "signal"
    signal_type: str  # "buy" or "sell"
    symbol: str
    price: Decimal
    shares: int
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrderEvent(TransactionEvent):
    """Order placed."""
    
    event_type: str = "order"
    order_type: OrderType
    symbol: str
    shares: int
    target_price: Decimal
    actual_price: Decimal
    slippage: Decimal
    commission: Decimal
    total_cost: Decimal
    cash_before: Decimal
    cash_after: Decimal
    reason: Optional[str] = None


class PositionUpdateEvent(TransactionEvent):
    """Position price updated."""
    
    event_type: str = "position_update"
    symbol: str
    shares: int
    entry_price: Decimal
    entry_date: datetime
    current_price: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal


class TradeCompletedEvent(TransactionEvent):
    """Trade completed (buy + sell)."""
    
    event_type: str = "trade_completed"
    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: Decimal
    exit_price: Decimal
    shares: int
    pnl: Decimal
    pnl_pct: Decimal
    holding_days: int
    total_cost: Decimal
    total_proceeds: Decimal


class PortfolioSnapshotEvent(TransactionEvent):
    """Daily portfolio snapshot."""
    
    event_type: str = "portfolio_snapshot"
    cash: Decimal
    positions_value: Decimal
    total_value: Decimal
    num_positions: int
    positions: list[dict[str, Any]]


class BacktestCompleteEvent(TransactionEvent):
    """Backtest completion event."""
    
    event_type: str = "backtest_complete"
    final_capital: Decimal
    total_return: Decimal
    total_return_pct: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    metrics: dict[str, Any]


class TransactionLogger:
    """Logger for all transaction events."""
    
    def __init__(self, output_file: Path):
        """Initialize transaction logger.
        
        Args:
            output_file: Path to JSON log file
        """
        self.output_file = output_file
        self.events: list[TransactionEvent] = []
        
    def log(self, event: TransactionEvent) -> None:
        """Log a transaction event.
        
        Args:
            event: Event to log
        """
        self.events.append(event)
    
    def save(self) -> None:
        """Save all events to JSON file."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert events to dictionaries
        events_data = [event.to_dict() for event in self.events]
        
        # Write to file with pretty formatting
        with open(self.output_file, 'w') as f:
            json.dump(events_data, f, indent=2, default=str)
    
    def load(self, file_path: Path) -> list[dict[str, Any]]:
        """Load events from JSON file.
        
        Args:
            file_path: Path to JSON log file
            
        Returns:
            List of event dictionaries
        """
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def get_events_by_type(self, event_type: str) -> list[TransactionEvent]:
        """Get all events of a specific type.
        
        Args:
            event_type: Type of event to filter
            
        Returns:
            List of matching events
        """
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_by_symbol(self, symbol: str) -> list[TransactionEvent]:
        """Get all events for a specific symbol.
        
        Args:
            symbol: Stock symbol to filter
            
        Returns:
            List of matching events
        """
        return [
            e for e in self.events 
            if hasattr(e, 'symbol') and getattr(e, 'symbol') == symbol
        ]

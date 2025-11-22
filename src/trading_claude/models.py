"""Core data models for the trading system."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class OrderType(str, Enum):
    """Type of order."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    """Status of an order."""

    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


class Order(BaseModel):
    """Represents a buy or sell order."""

    symbol: str
    order_type: OrderType
    shares: int = Field(gt=0)
    price: Decimal = Field(gt=0)
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING
    execution_price: Optional[Decimal] = None
    execution_timestamp: Optional[datetime] = None

    model_config = {"frozen": True}


class Position(BaseModel):
    """Represents a stock position in the portfolio."""

    symbol: str
    shares: int = Field(gt=0)
    entry_price: Decimal = Field(gt=0)
    entry_date: datetime
    current_price: Optional[Decimal] = None

    @property
    def cost_basis(self) -> Decimal:
        """Total cost of the position."""
        return self.entry_price * self.shares

    @property
    def current_value(self) -> Decimal:
        """Current value of the position."""
        price = self.current_price or self.entry_price
        return price * self.shares

    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized profit/loss."""
        return self.current_value - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> Decimal:
        """Unrealized profit/loss percentage."""
        if self.cost_basis == 0:
            return Decimal("0")
        return (self.unrealized_pnl / self.cost_basis) * 100

    def update_price(self, price: Decimal) -> "Position":
        """Update the current price of the position."""
        return self.model_copy(update={"current_price": price})


class Trade(BaseModel):
    """Represents a completed trade (buy + sell)."""

    symbol: str
    entry_date: datetime
    exit_date: datetime
    entry_price: Decimal = Field(gt=0)
    exit_price: Decimal = Field(gt=0)
    shares: int = Field(gt=0)
    pnl: Decimal
    pnl_pct: Decimal
    holding_days: int = Field(ge=0)

    @field_validator("pnl", mode="before")
    @classmethod
    def calculate_pnl(cls, v, info):
        """Calculate profit/loss if not provided."""
        if v is not None:
            return v
        data = info.data
        exit_value = data["exit_price"] * data["shares"]
        entry_value = data["entry_price"] * data["shares"]
        return exit_value - entry_value

    @field_validator("pnl_pct", mode="before")
    @classmethod
    def calculate_pnl_pct(cls, v, info):
        """Calculate profit/loss percentage if not provided."""
        if v is not None:
            return v
        data = info.data
        entry_value = data["entry_price"] * data["shares"]
        if entry_value == 0:
            return Decimal("0")
        exit_value = data["exit_price"] * data["shares"]
        return ((exit_value - entry_value) / entry_value) * 100

    @field_validator("holding_days", mode="before")
    @classmethod
    def calculate_holding_days(cls, v, info):
        """Calculate holding period if not provided."""
        if v is not None:
            return v
        data = info.data
        delta = data["exit_date"] - data["entry_date"]
        return delta.days


class PortfolioSnapshot(BaseModel):
    """Snapshot of portfolio state at a point in time."""

    timestamp: datetime
    cash: Decimal
    positions_value: Decimal
    total_value: Decimal
    positions: list[Position] = Field(default_factory=list)
    
    @property
    def num_positions(self) -> int:
        """Number of open positions."""
        return len(self.positions)

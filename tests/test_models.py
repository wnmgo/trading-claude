"""Test core data models."""

from datetime import datetime
from decimal import Decimal

import pytest

from trading_claude.models import Order, OrderType, Position, Trade


def test_position_creation():
    """Test Position creation and properties."""
    pos = Position(
        symbol="AAPL",
        shares=100,
        entry_price=Decimal("150.00"),
        entry_date=datetime(2024, 1, 1),
    )

    assert pos.symbol == "AAPL"
    assert pos.shares == 100
    assert pos.cost_basis == Decimal("15000.00")
    assert pos.current_value == Decimal("15000.00")  # No current_price set
    assert pos.unrealized_pnl == Decimal("0")


def test_position_with_current_price():
    """Test Position with current price update."""
    pos = Position(
        symbol="AAPL",
        shares=100,
        entry_price=Decimal("150.00"),
        entry_date=datetime(2024, 1, 1),
        current_price=Decimal("157.50"),
    )

    assert pos.current_value == Decimal("15750.00")
    assert pos.unrealized_pnl == Decimal("750.00")
    assert pos.unrealized_pnl_pct == Decimal("5.0")


def test_position_update_price():
    """Test Position price update method."""
    pos = Position(
        symbol="AAPL",
        shares=100,
        entry_price=Decimal("150.00"),
        entry_date=datetime(2024, 1, 1),
    )

    updated_pos = pos.update_price(Decimal("160.00"))
    assert updated_pos.current_price == Decimal("160.00")
    assert updated_pos.unrealized_pnl_pct == Decimal("10.0") / Decimal("1.5")


def test_trade_creation():
    """Test Trade creation with calculated fields."""
    trade = Trade(
        symbol="AAPL",
        entry_date=datetime(2024, 1, 1),
        exit_date=datetime(2024, 1, 15),
        entry_price=Decimal("150.00"),
        exit_price=Decimal("157.50"),
        shares=100,
        pnl=Decimal("750.00"),
        pnl_pct=Decimal("5.0"),
        holding_days=14,
    )

    assert trade.symbol == "AAPL"
    assert trade.pnl == Decimal("750.00")
    assert trade.pnl_pct == Decimal("5.0")
    assert trade.holding_days == 14


def test_order_creation():
    """Test Order creation."""
    order = Order(
        symbol="AAPL",
        order_type=OrderType.BUY,
        shares=100,
        price=Decimal("150.00"),
        timestamp=datetime(2024, 1, 1),
    )

    assert order.symbol == "AAPL"
    assert order.order_type == OrderType.BUY
    assert order.shares == 100
    assert order.price == Decimal("150.00")

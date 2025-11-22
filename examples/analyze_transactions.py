"""Example script to analyze transaction log files.

This demonstrates how to:
1. Load and parse transaction logs
2. Verify trades follow the strategy
3. Extract specific events for analysis
"""

import json
import sys
from decimal import Decimal
from pathlib import Path


def load_transaction_log(file_path: Path) -> list[dict]:
    """Load transaction log from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def verify_strategy_compliance(events: list[dict]) -> dict:
    """Verify all trades follow the strategy rules.
    
    Returns:
        Dictionary with compliance results
    """
    # Get strategy config
    init_event = next(e for e in events if e['event_type'] == 'backtest_init')
    strategy_config = init_event['strategy_config']
    gain_threshold = Decimal(strategy_config['gain_threshold_pct'])
    
    # Check all completed trades
    trade_events = [e for e in events if e['event_type'] == 'trade_completed']
    
    violations = []
    for trade in trade_events:
        pnl_pct = Decimal(trade['pnl_pct'])
        
        # Check if trade exited at correct gain threshold
        if pnl_pct < gain_threshold:
            violations.append({
                'trade': trade,
                'violation': f"Exited at {pnl_pct}% (threshold: {gain_threshold}%)",
            })
    
    return {
        'total_trades': len(trade_events),
        'violations': violations,
        'compliant': len(violations) == 0,
        'compliance_rate': (len(trade_events) - len(violations)) / len(trade_events) * 100 if trade_events else 0,
    }


def print_trade_summary(events: list[dict]) -> None:
    """Print a summary of all trades."""
    trade_events = [e for e in events if e['event_type'] == 'trade_completed']
    
    print("\n" + "=" * 80)
    print("TRADE SUMMARY")
    print("=" * 80)
    print(f"\nTotal Trades: {len(trade_events)}\n")
    
    for i, trade in enumerate(trade_events, 1):
        print(f"Trade {i}: {trade['symbol']}")
        print(f"  Entry: {trade['entry_date'][:10]} @ ${trade['entry_price']}")
        print(f"  Exit:  {trade['exit_date'][:10]} @ ${trade['exit_price']}")
        print(f"  Shares: {trade['shares']}")
        print(f"  P&L: ${trade['pnl']} ({trade['pnl_pct']}%)")
        print(f"  Holding Period: {trade['holding_days']} days")
        print()


def print_signal_analysis(events: list[dict]) -> None:
    """Analyze buy/sell signals."""
    signal_events = [e for e in events if e['event_type'] == 'signal']
    
    buy_signals = [e for e in signal_events if e['signal_type'] == 'buy']
    sell_signals = [e for e in signal_events if e['signal_type'] == 'sell']
    
    # Match with actual orders
    order_events = [e for e in events if e['event_type'] == 'order']
    buy_orders = [e for e in order_events if e['order_type'] == 'BUY']
    sell_orders = [e for e in order_events if e['order_type'] == 'SELL']
    
    print("\n" + "=" * 80)
    print("SIGNAL ANALYSIS")
    print("=" * 80)
    print(f"\nBuy Signals Generated: {len(buy_signals)}")
    print(f"Buy Orders Executed: {len(buy_orders)}")
    print(f"Execution Rate: {len(buy_orders) / len(buy_signals) * 100:.1f}%")
    
    print(f"\nSell Signals Generated: {len(sell_signals)}")
    print(f"Sell Orders Executed: {len(sell_orders)}")
    print(f"Execution Rate: {len(sell_orders) / len(sell_signals) * 100:.1f}%")
    
    # Signals that didn't execute
    if len(buy_signals) > len(buy_orders):
        print(f"\nUnexecuted Buy Signals: {len(buy_signals) - len(buy_orders)}")
        executed_symbols = {o['symbol'] for o in buy_orders}
        for signal in buy_signals:
            if signal['symbol'] not in executed_symbols:
                print(f"  • {signal['symbol']} @ ${signal['price']} ({signal['shares']} shares)")
                print(f"    Reason: Likely insufficient cash")


def print_slippage_analysis(events: list[dict]) -> None:
    """Analyze slippage and commissions."""
    order_events = [e for e in events if e['event_type'] == 'order']
    
    total_slippage = sum(Decimal(e['slippage']) * e['shares'] for e in order_events)
    total_commission = sum(Decimal(e['commission']) for e in order_events)
    
    print("\n" + "=" * 80)
    print("COST ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Slippage: ${total_slippage:.2f}")
    print(f"Total Commission: ${total_commission:.2f}")
    print(f"Total Trading Costs: ${total_slippage + total_commission:.2f}")
    
    # Average slippage per trade
    if order_events:
        avg_slippage = total_slippage / len(order_events)
        print(f"Average Slippage per Order: ${avg_slippage:.2f}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_transactions.py <transaction_log.json>")
        sys.exit(1)
    
    log_file = Path(sys.argv[1])
    if not log_file.exists():
        print(f"Error: File not found: {log_file}")
        sys.exit(1)
    
    # Load transaction log
    print(f"Loading transaction log: {log_file}")
    events = load_transaction_log(log_file)
    
    # Get backtest info
    init_event = next(e for e in events if e['event_type'] == 'backtest_init')
    complete_event = next(e for e in events if e['event_type'] == 'backtest_complete')
    
    print("\n" + "=" * 80)
    print("BACKTEST INFORMATION")
    print("=" * 80)
    print(f"\nStrategy: {init_event['strategy_name']}")
    print(f"Period: {init_event['start_date'][:10]} to {init_event['end_date'][:10]}")
    print(f"Initial Capital: ${init_event['initial_capital']}")
    print(f"Final Capital: ${complete_event['final_capital']}")
    print(f"Total Return: ${complete_event['total_return']} ({complete_event['total_return_pct']}%)")
    
    # Verify strategy compliance
    print("\n" + "=" * 80)
    print("STRATEGY COMPLIANCE")
    print("=" * 80)
    
    compliance = verify_strategy_compliance(events)
    print(f"\nTotal Trades: {compliance['total_trades']}")
    print(f"Compliant Trades: {compliance['total_trades'] - len(compliance['violations'])}")
    print(f"Violations: {len(compliance['violations'])}")
    print(f"Compliance Rate: {compliance['compliance_rate']:.1f}%")
    
    if compliance['violations']:
        print("\nViolations:")
        for v in compliance['violations']:
            print(f"  • {v['trade']['symbol']}: {v['violation']}")
    
    # Print other analyses
    print_trade_summary(events)
    print_signal_analysis(events)
    print_slippage_analysis(events)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal Events Logged: {len(events)}")
    print(f"Event Types:")
    event_types = {}
    for e in events:
        event_types[e['event_type']] = event_types.get(e['event_type'], 0) + 1
    for event_type, count in sorted(event_types.items()):
        print(f"  • {event_type}: {count}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()

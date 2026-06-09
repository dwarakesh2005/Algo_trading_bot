import logging
from config import MAX_POSITION_PCT, MAX_POSITIONS, BROKERAGE_PCT
from database import (
    get_portfolio, save_portfolio,
    get_open_positions, open_position, close_position,
    log_trade,
)

logger = logging.getLogger(__name__)


def _brokerage(amount: float) -> float:
    return round(amount * BROKERAGE_PCT, 2)


# ── BUY ───────────────────────────────────────────────────────────────────────

def execute_buy(symbol: str, price: float) -> dict:
    """
    Attempt to open a new paper position.
    Returns {"success": bool, ...details}
    """
    portfolio  = get_portfolio()
    positions  = get_open_positions()

    # Guards
    if symbol in positions:
        return {"success": False, "reason": f"{symbol} already held"}

    if len(positions) >= MAX_POSITIONS:
        return {"success": False, "reason": "Max positions reached"}

    cash = float(portfolio["cash"])
    portfolio_value = float(portfolio["total_value"])

    # Position sizing: 10% of total portfolio value
    target_invest = portfolio_value * MAX_POSITION_PCT
    invest_amount = min(target_invest, cash * 0.97)   # never use > 97% of remaining cash

    if invest_amount < 5_000:
        return {"success": False, "reason": "Insufficient cash"}

    brok      = _brokerage(invest_amount)
    qty       = int((invest_amount - brok) / price)

    if qty < 1:
        return {"success": False, "reason": "Price too high for 1 share"}

    total_cost = qty * price + brok
    new_cash   = cash - total_cost

    # Persist
    open_position(symbol, qty, price)
    log_trade(symbol, "BUY", qty, price)

    # Recalculate portfolio value
    all_pos  = get_open_positions()
    pos_value = sum(p["quantity"] * p["current_price"] for p in all_pos.values())
    save_portfolio(new_cash, new_cash + pos_value)

    logger.info(f"BUY  {symbol} x{qty} @ ₹{price:.2f} | cost ₹{total_cost:,.0f}")
    return {
        "success": True,
        "symbol":  symbol,
        "qty":     qty,
        "price":   price,
        "cost":    round(total_cost, 2),
    }


# ── SELL ──────────────────────────────────────────────────────────────────────

def execute_sell(symbol: str, price: float) -> dict:
    """
    Close an existing paper position.
    Returns {"success": bool, ...details}
    """
    positions = get_open_positions()

    if symbol not in positions:
        return {"success": False, "reason": f"No open position for {symbol}"}

    pos       = positions[symbol]
    qty       = int(pos["quantity"])
    buy_price = float(pos["buy_price"])
    pos_id    = pos["id"]

    proceeds  = qty * price
    brok      = _brokerage(proceeds)
    net_proceeds = proceeds - brok
    pnl       = round(net_proceeds - (qty * buy_price), 2)

    # Persist
    close_position(pos_id, price, pnl)
    log_trade(symbol, "SELL", qty, price, pnl)

    # Recalculate portfolio
    portfolio  = get_portfolio()
    new_cash   = float(portfolio["cash"]) + net_proceeds
    remaining  = {s: p for s, p in get_open_positions().items()}
    pos_value  = sum(p["quantity"] * p["current_price"] for p in remaining.values())
    save_portfolio(new_cash, new_cash + pos_value)

    logger.info(f"SELL {symbol} x{qty} @ ₹{price:.2f} | P&L ₹{pnl:+,.0f}")
    return {
        "success": True,
        "symbol":  symbol,
        "qty":     qty,
        "price":   price,
        "pnl":     pnl,
    }


# ── Batch processor ───────────────────────────────────────────────────────────

def process_signals(signals: dict[str, dict]) -> dict:
    """
    Given a {symbol: signal_dict} map, execute all BUY/SELL orders.
    SELLs are processed first to free up cash before BUYs.
    Returns summary {"bought": [...], "sold": [...], "skipped": [...]}
    """
    positions = get_open_positions()
    summary   = {"bought": [], "sold": [], "skipped": []}

    sell_list = [(s, sig) for s, sig in signals.items() if sig["signal"] == "SELL" and s in positions]
    buy_list  = [(s, sig) for s, sig in signals.items() if sig["signal"] == "BUY"  and s not in positions]

    # ── Execute SELLs ──────────────────────────────────────────────────────────
    for symbol, sig in sell_list:
        result = execute_sell(symbol, sig["price"])
        if result["success"]:
            summary["sold"].append(result)
        else:
            summary["skipped"].append({"symbol": symbol, "reason": result["reason"]})

    # ── Execute BUYs ───────────────────────────────────────────────────────────
    for symbol, sig in buy_list:
        result = execute_buy(symbol, sig["price"])
        if result["success"]:
            summary["bought"].append(result)
        else:
            summary["skipped"].append({"symbol": symbol, "reason": result["reason"]})

    return summary

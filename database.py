from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, INITIAL_CAPITAL
from datetime import date
import logging

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── Portfolio ─────────────────────────────────────────────────────────────────

def get_portfolio() -> dict:
    """Return the latest portfolio snapshot. Seeds initial capital if empty."""
    db = get_client()
    res = db.table("portfolio").select("*").order("id", desc=True).limit(1).execute()

    if res.data:
        return res.data[0]

    # First run — seed the portfolio
    seed = {"cash": INITIAL_CAPITAL, "total_value": INITIAL_CAPITAL, "date": str(date.today())}
    db.table("portfolio").insert(seed).execute()
    return seed


def save_portfolio(cash: float, total_value: float) -> None:
    get_client().table("portfolio").insert({
        "cash":        round(cash, 2),
        "total_value": round(total_value, 2),
        "date":        str(date.today()),
    }).execute()


# ── Positions ─────────────────────────────────────────────────────────────────

def get_open_positions() -> dict[str, dict]:
    """Return all currently active positions as {symbol: row}."""
    db  = get_client()
    res = db.table("positions").select("*").eq("active", True).execute()
    return {row["symbol"]: row for row in (res.data or [])}


def open_position(symbol: str, qty: int, buy_price: float) -> None:
    get_client().table("positions").insert({
        "symbol":        symbol,
        "quantity":      qty,
        "buy_price":     round(buy_price, 2),
        "current_price": round(buy_price, 2),
        "active":        True,
        "open_date":     str(date.today()),
    }).execute()


def close_position(position_id: int, sell_price: float, pnl: float) -> None:
    get_client().table("positions").update({
        "active":        False,
        "current_price": round(sell_price, 2),
        "sell_price":    round(sell_price, 2),
        "pnl":           round(pnl, 2),
        "close_date":    str(date.today()),
    }).eq("id", position_id).execute()


def refresh_position_prices(positions: dict[str, dict], latest_prices: dict[str, float]) -> None:
    """Update the current_price of every open position to reflect today's close."""
    db = get_client()
    for symbol, pos in positions.items():
        if symbol in latest_prices:
            db.table("positions").update({
                "current_price": round(latest_prices[symbol], 2),
            }).eq("id", pos["id"]).execute()


# ── Trades ────────────────────────────────────────────────────────────────────

def log_trade(symbol: str, action: str, qty: int, price: float, pnl: float = 0.0) -> None:
    get_client().table("trades").insert({
        "symbol":   symbol,
        "action":   action,
        "quantity": qty,
        "price":    round(price, 2),
        "pnl":      round(pnl, 2),
        "date":     str(date.today()),
    }).execute()


def get_today_trades() -> list[dict]:
    res = get_client().table("trades").select("*").eq("date", str(date.today())).execute()
    return res.data or []


def get_all_closed_trades() -> list[dict]:
    res = get_client().table("trades").select("*").eq("action", "SELL").execute()
    return res.data or []


# ── Summary stats ─────────────────────────────────────────────────────────────

def get_trade_stats() -> dict:
    trades = get_all_closed_trades()
    if not trades:
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "realized_pnl": 0.0}

    wins   = [t for t in trades if t.get("pnl", 0) > 0]
    losses = [t for t in trades if t.get("pnl", 0) <= 0]

    return {
        "total":        len(trades),
        "wins":         len(wins),
        "losses":       len(losses),
        "win_rate":     round(len(wins) / len(trades) * 100, 1),
        "realized_pnl": round(sum(t.get("pnl", 0) for t in trades), 2),
    }

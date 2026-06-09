import requests
import logging
from datetime import date
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, INITIAL_CAPITAL
from database import get_portfolio, get_open_positions, get_today_trades, get_trade_stats

logger = logging.getLogger(__name__)


# ── Formatting helpers ────────────────────────────────────────────────────────

def _pnl_str(pnl: float) -> str:
    emoji = "🟢" if pnl >= 0 else "🔴"
    sign  = "+" if pnl >= 0 else ""
    return f"{emoji} {sign}₹{abs(pnl):,.0f}"


def _pct(pnl: float, base: float) -> str:
    if base == 0:
        return "0.00%"
    p   = pnl / base * 100
    sgn = "+" if p >= 0 else ""
    return f"{sgn}{p:.2f}%"


# ── Report builder ────────────────────────────────────────────────────────────

def build_report() -> str:
    portfolio = get_portfolio()
    positions = get_open_positions()
    trades    = get_today_trades()
    stats     = get_trade_stats()

    cash        = float(portfolio["cash"])
    total_value = float(portfolio["total_value"])
    total_pnl   = total_value - INITIAL_CAPITAL
    today_str   = date.today().strftime("%d %b %Y")

    # ── Header ──────────────────────────────────────────────────────────────
    lines = [
        f"📊 <b>NSE Paper Trading — {today_str}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"💰 <b>Portfolio:</b>  ₹{total_value:,.0f}",
        f"💵 <b>Cash:</b>       ₹{cash:,.0f}",
        f"📈 <b>Total P&amp;L:</b>  {_pnl_str(total_pnl)} <i>({_pct(total_pnl, INITIAL_CAPITAL)})</i>",
        "",
    ]

    # ── Today's trades ───────────────────────────────────────────────────────
    if trades:
        lines.append("🔄 <b>TODAY'S TRADES:</b>")
        for t in trades:
            action = "🟢 BUY " if t["action"] == "BUY" else "🔴 SELL"
            pnl_part = f"  →  {_pnl_str(t['pnl'])}" if t["action"] == "SELL" else ""
            lines.append(
                f"  {action}  <code>{t['symbol']:<14}</code>"
                f" ×{t['quantity']}  @₹{t['price']:,.2f}{pnl_part}"
            )
    else:
        lines.append("📭 <b>No trades today</b>  <i>(no crossover signal)</i>")

    lines.append("")

    # ── Open positions ───────────────────────────────────────────────────────
    if positions:
        lines.append(f"📂 <b>OPEN POSITIONS ({len(positions)}/{8}):</b>")
        for sym, pos in positions.items():
            qty      = int(pos["quantity"])
            bp       = float(pos["buy_price"])
            cp       = float(pos["current_price"])
            unrl_pnl = (cp - bp) * qty
            pct_str  = _pct(unrl_pnl, bp * qty)
            lines.append(
                f"  <code>{sym:<14}</code> ×{qty}  "
                f"bp:₹{bp:,.0f} → ₹{cp:,.0f}  {_pnl_str(unrl_pnl)} <i>({pct_str})</i>"
            )
    else:
        lines.append("📂 <b>No open positions</b>")

    lines.append("")

    # ── Stats footer ─────────────────────────────────────────────────────────
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"🏆 <b>Win Rate:</b>  {stats['wins']}W / {stats['losses']}L  ({stats['win_rate']}%)",
        f"💹 <b>Realised P&amp;L:</b>  {_pnl_str(stats['realized_pnl'])}",
        f"📦 <b>Total Trades:</b>  {stats['total']}",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        "<i>Strategy: EMA 9/21 Crossover + RSI(14)</i>",
        "<i>Data: NSE via yfinance  |  Paper Trading Only 🎭</i>",
    ]

    return "\n".join(lines)


# ── Sender ────────────────────────────────────────────────────────────────────

def send_report(message: str | None = None) -> bool:
    if message is None:
        message = build_report()

    url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("✅ Telegram report sent")
        return True
    except Exception as e:
        logger.error(f"❌ Telegram send failed: {e}")
        return False


def send_alert(text: str) -> bool:
    """Send a short alert message (e.g. trade executed)."""
    return send_report(f"🔔 <b>Alert</b>\n{text}")

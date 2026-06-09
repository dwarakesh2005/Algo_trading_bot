"""
main.py — NSE Paper Trading Bot
─────────────────────────────────────────────────────────────────
Daily pipeline (runs via GitHub Actions at 3:45 PM IST):

  1. Fetch EOD data for all NIFTY 50 watchlist stocks (yfinance)
  2. Calculate EMA 9/21 crossover + RSI(14) signals
  3. Execute BUY / SELL on the virtual ₹10L portfolio
  4. Refresh unrealised P&L on open positions
  5. Send daily summary report to Telegram
─────────────────────────────────────────────────────────────────
"""

import logging
import sys
from config import WATCHLIST
from data_fetcher import fetch_watchlist
from strategy import scan_signals
from paper_trader import process_signals
from database import get_open_positions, refresh_position_prices
from reporter import send_report, build_report

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("═══════════════════════════════════════")
    logger.info("  NSE Paper Trading Bot  —  Starting   ")
    logger.info("═══════════════════════════════════════")

    # ── Step 1: Fetch market data ─────────────────────────────────────────────
    logger.info(f"📡 Fetching data for {len(WATCHLIST)} stocks...")
    stock_data = fetch_watchlist(WATCHLIST)

    if not stock_data:
        logger.error("No market data retrieved. Aborting.")
        send_report("⚠️ <b>Bot Error</b>\nCould not fetch market data from yfinance. Check logs.")
        sys.exit(1)

    # ── Step 2: Generate signals ──────────────────────────────────────────────
    logger.info("📊 Generating strategy signals...")
    signals = scan_signals(stock_data)

    buy_count  = sum(1 for s in signals.values() if s["signal"] == "BUY")
    sell_count = sum(1 for s in signals.values() if s["signal"] == "SELL")
    logger.info(f"   Signals → BUY: {buy_count}  SELL: {sell_count}  HOLD: {len(signals)-buy_count-sell_count}")

    # ── Step 3: Execute paper trades ──────────────────────────────────────────
    logger.info("💼 Processing trades...")
    summary = process_signals(signals)

    for t in summary["sold"]:
        logger.info(f"  SOLD  {t['symbol']} ×{t['qty']} @ ₹{t['price']:.2f}  P&L: ₹{t['pnl']:+,.0f}")
    for t in summary["bought"]:
        logger.info(f"  BOUGHT {t['symbol']} ×{t['qty']} @ ₹{t['price']:.2f}")
    for s in summary["skipped"]:
        logger.info(f"  SKIP   {s['symbol']}: {s['reason']}")

    # ── Step 4: Refresh unrealised P&L ────────────────────────────────────────
    logger.info("🔄 Refreshing open position prices...")
    open_positions = get_open_positions()
    latest_prices  = {sym: float(data["close"].iloc[-1]) for sym, data in stock_data.items()}
    refresh_position_prices(open_positions, latest_prices)

    # ── Step 5: Send Telegram report ──────────────────────────────────────────
    logger.info("📨 Sending Telegram daily report...")
    report  = build_report()
    success = send_report(report)

    if success:
        logger.info("✅ Done! Report delivered.")
    else:
        logger.error("❌ Report delivery failed.")
        sys.exit(1)

    logger.info("═══════════════════════════════════════")


if __name__ == "__main__":
    main()

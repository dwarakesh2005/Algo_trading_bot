import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ───────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ── Supabase ───────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ── Virtual Portfolio ──────────────────────────────────────
INITIAL_CAPITAL    = 1_000_000   # ₹10 Lakhs virtual money
MAX_POSITION_PCT   = 0.10        # Max 10% of portfolio per trade
MAX_POSITIONS      = 8           # Max concurrent open positions
BROKERAGE_PCT      = 0.0003      # 0.03% simulated brokerage per side

# ── Strategy Parameters ────────────────────────────────────
EMA_SHORT         = 9
EMA_LONG          = 21
RSI_PERIOD        = 14
RSI_BUY_MAX       = 65           # Don't buy if RSI is above this
RSI_SELL_MIN      = 75           # Force sell if RSI crosses above this
VOLUME_MA_PERIOD  = 20
VOLUME_FACTOR     = 1.2          # Volume must be 1.2x the 20-day avg

# ── NIFTY 50 Watchlist (NSE symbols) ──────────────────────
WATCHLIST = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "BAJFINANCE", "ASIANPAINT", "AXISBANK", "MARUTI",
    "SUNPHARMA", "TITAN", "WIPRO", "ULTRACEMCO", "HCLTECH",
    "POWERGRID", "NTPC", "JSWSTEEL", "TATASTEEL", "TECHM",
    "DIVISLAB", "BAJAJFINSV", "GRASIM", "ADANIENT", "NESTLEIND",
]

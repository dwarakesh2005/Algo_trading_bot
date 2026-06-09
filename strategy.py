import pandas as pd
import numpy as np
from config import (
    EMA_SHORT, EMA_LONG, RSI_PERIOD,
    RSI_BUY_MAX, RSI_SELL_MIN,
    VOLUME_MA_PERIOD, VOLUME_FACTOR,
)


# ── Indicator helpers ──────────────────────────────────────────────────────────

def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(window=period).mean()
    loss  = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ── Signal generator ───────────────────────────────────────────────────────────

def generate_signal(df: pd.DataFrame) -> dict:
    """
    Analyse a stock's OHLCV DataFrame and return a signal dict:
        {
            "signal":  "BUY" | "SELL" | "HOLD",
            "price":   float,          # latest close
            "rsi":     float,
            "ema_short": float,
            "ema_long":  float,
            "reason":  str,
        }
    Requires at least EMA_LONG + 10 rows of data.
    """
    min_rows = EMA_LONG + 10
    if df is None or len(df) < min_rows:
        return {"signal": "HOLD", "reason": "Insufficient data", "price": 0.0}

    df = df.copy()

    # Calculate indicators
    df["ema_s"]   = ema(df["close"], EMA_SHORT)
    df["ema_l"]   = ema(df["close"], EMA_LONG)
    df["rsi_val"] = rsi(df["close"], RSI_PERIOD)
    df["vol_avg"] = df["volume"].rolling(window=VOLUME_MA_PERIOD).mean()

    curr = df.iloc[-1]
    prev = df.iloc[-2]

    price      = float(curr["close"])
    rsi_now    = float(curr["rsi_val"])
    ema_s_now  = float(curr["ema_s"])
    ema_l_now  = float(curr["ema_l"])
    vol_ok     = float(curr["volume"]) > float(curr["vol_avg"]) * VOLUME_FACTOR

    # Crossover detection
    bullish_cross = float(prev["ema_s"]) <= float(prev["ema_l"]) and ema_s_now > ema_l_now
    bearish_cross = float(prev["ema_s"]) >= float(prev["ema_l"]) and ema_s_now < ema_l_now

    base = {
        "price":     round(price, 2),
        "rsi":       round(rsi_now, 2),
        "ema_short": round(ema_s_now, 2),
        "ema_long":  round(ema_l_now, 2),
    }

    # ── BUY ───────────────────────────────────────────────────────────────────
    if bullish_cross and rsi_now < RSI_BUY_MAX and vol_ok:
        return {**base, "signal": "BUY",  "reason": "EMA9 ↑ crosses EMA21 | RSI OK | Volume confirmed"}

    if bullish_cross and rsi_now < RSI_BUY_MAX and not vol_ok:
        return {**base, "signal": "BUY",  "reason": "EMA9 ↑ crosses EMA21 | RSI OK (low volume)"}

    # ── SELL ──────────────────────────────────────────────────────────────────
    if bearish_cross:
        return {**base, "signal": "SELL", "reason": "EMA9 ↓ crosses below EMA21"}

    if rsi_now > RSI_SELL_MIN:
        return {**base, "signal": "SELL", "reason": f"RSI overbought ({rsi_now:.1f})"}

    # ── HOLD ──────────────────────────────────────────────────────────────────
    return {**base, "signal": "HOLD", "reason": "No crossover signal"}


def scan_signals(stock_data: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """
    Run generate_signal on every stock and return a full dict:
        { symbol: signal_dict }
    """
    return {symbol: generate_signal(df) for symbol, df in stock_data.items()}

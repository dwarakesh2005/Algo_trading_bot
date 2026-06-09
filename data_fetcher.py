import yfinance as yf
import pandas as pd
import time
import logging

logger = logging.getLogger(__name__)


def fetch_stock_data(symbol: str, period: str = "6mo") -> pd.DataFrame | None:
    """
    Fetch daily OHLCV data for an NSE stock via yfinance.
    Appends .NS suffix automatically.
    Returns a clean DataFrame or None on failure.
    """
    ticker = f"{symbol}.NS"
    try:
        df = yf.download(
            ticker,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            multi_level_index=False,   # flat columns in yfinance v1.0
        )

        if df is None or df.empty:
            logger.warning(f"No data returned for {symbol}")
            return None

        # Normalize column names to lowercase
        df.columns = [c.lower() for c in df.columns]

        # Drop rows where Close is NaN (trading holidays / data gaps)
        df = df.dropna(subset=["close"])

        if len(df) < 30:
            logger.warning(f"Insufficient history for {symbol} ({len(df)} rows)")
            return None

        return df

    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return None


def fetch_watchlist(symbols: list[str], delay: float = 0.3) -> dict[str, pd.DataFrame]:
    """
    Fetch data for every symbol in the watchlist.
    Small delay between requests to avoid Yahoo rate-limits.
    Returns a dict of {symbol: DataFrame} for successful fetches only.
    """
    results: dict[str, pd.DataFrame] = {}

    for symbol in symbols:
        df = fetch_stock_data(symbol)
        if df is not None:
            results[symbol] = df
            logger.info(f"✅ {symbol}: {len(df)} candles loaded")
        else:
            logger.warning(f"⚠️  {symbol}: skipped")
        time.sleep(delay)

    logger.info(f"Fetched data for {len(results)}/{len(symbols)} stocks")
    return results


def get_latest_price(symbol: str) -> float | None:
    """Quick helper — returns the latest closing price for a symbol."""
    df = fetch_stock_data(symbol, period="5d")
    if df is not None and not df.empty:
        return float(df["close"].iloc[-1])
    return None

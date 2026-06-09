-- ═══════════════════════════════════════════════════════════════
--  NSE Paper Trading Bot  —  Supabase Schema
--  Run this once in your Supabase SQL editor.
-- ═══════════════════════════════════════════════════════════════


-- ── 1. Portfolio snapshots ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS portfolio (
    id          BIGSERIAL PRIMARY KEY,
    cash        NUMERIC(15, 2)  NOT NULL,
    total_value NUMERIC(15, 2)  NOT NULL,
    date        DATE            NOT NULL DEFAULT CURRENT_DATE,
    created_at  TIMESTAMPTZ     DEFAULT NOW()
);

-- Seed with ₹10L virtual capital
INSERT INTO portfolio (cash, total_value, date)
VALUES (1000000.00, 1000000.00, CURRENT_DATE)
ON CONFLICT DO NOTHING;


-- ── 2. Positions ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS positions (
    id            BIGSERIAL PRIMARY KEY,
    symbol        VARCHAR(20)     NOT NULL,
    quantity      INTEGER         NOT NULL,
    buy_price     NUMERIC(10, 2)  NOT NULL,
    current_price NUMERIC(10, 2),
    sell_price    NUMERIC(10, 2),
    pnl           NUMERIC(15, 2)  DEFAULT 0,
    active        BOOLEAN         DEFAULT TRUE,
    open_date     DATE            NOT NULL DEFAULT CURRENT_DATE,
    close_date    DATE,
    created_at    TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_positions_active ON positions(active);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);


-- ── 3. Trade log ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trades (
    id         BIGSERIAL PRIMARY KEY,
    symbol     VARCHAR(20)     NOT NULL,
    action     VARCHAR(4)      NOT NULL CHECK (action IN ('BUY', 'SELL')),
    quantity   INTEGER         NOT NULL,
    price      NUMERIC(10, 2)  NOT NULL,
    pnl        NUMERIC(15, 2)  DEFAULT 0,
    date       DATE            NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trades_date   ON trades(date);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_action ON trades(action);


-- ── Useful views ───────────────────────────────────────────────────────────

-- Open positions with unrealised P&L
CREATE OR REPLACE VIEW v_open_positions AS
SELECT
    symbol,
    quantity,
    buy_price,
    current_price,
    ROUND((current_price - buy_price) * quantity, 2)           AS unrealised_pnl,
    ROUND(((current_price - buy_price) / buy_price) * 100, 2)  AS pct_change,
    open_date
FROM positions
WHERE active = TRUE
ORDER BY open_date;

-- Overall stats
CREATE OR REPLACE VIEW v_stats AS
SELECT
    COUNT(*)                                    AS total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)   AS wins,
    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END)  AS losses,
    ROUND(SUM(pnl), 2)                          AS realized_pnl,
    ROUND(AVG(pnl), 2)                          AS avg_pnl_per_trade,
    ROUND(
        SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(*), 0) * 100,
        1
    )                                           AS win_rate_pct
FROM trades
WHERE action = 'SELL';

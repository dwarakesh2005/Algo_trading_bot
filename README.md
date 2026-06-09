# 🇮🇳 NSE Algo Paper Trading Bot

Fully automated paper trading system for NSE (NIFTY 50) using Python.
Runs on **100% free services** — no credit card, no static IP required.

---

## 📦 Tech Stack

| Layer         | Tool            | Cost   |
|---------------|-----------------|--------|
| Market Data   | yfinance (NSE)  | Free   |
| Storage       | Supabase        | Free   |
| Scheduler     | GitHub Actions  | Free   |
| Notifications | Telegram Bot    | Free   |

---

## 🏗️ Strategy

- **EMA 9 / EMA 21 crossover** — BUY on bullish cross, SELL on bearish cross
- **RSI(14) filter** — only buy when RSI < 65, force-sell above 75
- **Volume confirmation** — volume must be ≥ 1.2× 20-day average
- **Position sizing** — 10% of portfolio per trade, max 8 concurrent positions
- **Virtual capital** — ₹10,00,000 (₹10 Lakhs)

---

## ⚙️ Setup (one-time, ~20 mins)

### Step 1 — Create your Telegram Bot

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow prompts → copy your **BOT TOKEN**
3. Start a chat with your new bot
4. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` in your browser
5. Send any message to your bot, refresh the URL → copy your **chat_id**

### Step 2 — Set up Supabase

1. Go to [supabase.com](https://supabase.com) → create a free project
2. Open **SQL Editor** → paste the contents of `supabase_schema.sql` → Run
3. Go to **Project Settings → API** → copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon / public key** → `SUPABASE_KEY`

### Step 3 — Set up GitHub

1. Fork or push this repo to your GitHub account
2. Go to **Settings → Secrets and variables → Actions**
3. Add these 4 secrets:

| Secret Name        | Value                        |
|--------------------|------------------------------|
| `TELEGRAM_TOKEN`   | From Step 1                  |
| `TELEGRAM_CHAT_ID` | From Step 1                  |
| `SUPABASE_URL`     | From Step 2                  |
| `SUPABASE_KEY`     | From Step 2                  |

4. That's it! The bot will run automatically every weekday at **3:45 PM IST**.

---

## 🧪 Local Testing

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/nse-paper-trader
cd nse-paper-trader

# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Fill in your actual values in .env

# Run manually
python main.py
```

---

## 📁 Project Structure

```
nse-paper-trader/
├── .github/workflows/trading.yml   ← GitHub Actions schedule
├── config.py                       ← All settings & watchlist
├── data_fetcher.py                 ← yfinance NSE data
├── strategy.py                     ← EMA + RSI signals
├── paper_trader.py                 ← Virtual buy/sell engine
├── database.py                     ← Supabase CRUD
├── reporter.py                     ← Telegram report builder
├── main.py                         ← Orchestrator
├── requirements.txt
├── supabase_schema.sql             ← Run once in Supabase
└── .env.example
```

---

## 📨 Sample Daily Report

```
📊 NSE Paper Trading — 10 Jun 2026
━━━━━━━━━━━━━━━━━━━━━━━
💰 Portfolio:   ₹10,43,250
💵 Cash:        ₹5,12,800
📈 Total P&L:   🟢 +₹43,250 (+4.33%)

🔄 TODAY'S TRADES:
  🟢 BUY   INFY           ×5  @₹1,842.00
  🔴 SELL  TCS            ×3  @₹3,910.00  →  🟢 +₹2,100

📂 OPEN POSITIONS (3/8):
  RELIANCE       ×10  bp:₹2,810 → ₹2,945  🟢 +₹1,350 (+4.8%)
  HDFCBANK       ×8   bp:₹1,620 → ₹1,598  🔴 -₹176 (-1.4%)
  INFY           ×5   bp:₹1,842 → ₹1,842  🟢 +₹0 (0.0%)

━━━━━━━━━━━━━━━━━━━━━━━
🏆 Win Rate:  7W / 3L  (70.0%)
💹 Realised P&L:  🟢 +₹18,400
📦 Total Trades:  10
```

---

## ⚠️ Disclaimer

This is a **paper trading simulation** — no real money is involved.
For educational and research purposes only. Not financial advice.

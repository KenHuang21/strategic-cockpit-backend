# Strategic Cockpit - Backend

Backend data fetching and processing for the Strategic Cockpit dashboard.

## Features

- **Economic Calendar Scraper** (`fetch_calendar.py`)
  - Fetches US High/Medium impact economic events
  - 4-week rolling window
  - Dual-trigger Telegram notifications
  - Automated via GitHub Actions (hourly)

- **Metrics Fetcher** (`fetch_metrics.py`)  
  - BTC price, stablecoin market cap, RWA TVL
  - US 10Y yield, Fed net liquidity
  - Threshold-based notifications
  - Runs every 15 minutes

## Setup

### Prerequisites
- Python 3.9+
- Telegram bot (for notifications)
- FRED API key (for economic data)

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export FRED_API_KEY="your_fred_api_key"
```

### GitHub Secrets

Add these to your repository settings:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `FRED_API_KEY`

## Usage

### Manual Execution

```bash
# Fetch economic calendar (4-week range)
python fetch_calendar.py

# Fetch dashboard metrics
python fetch_metrics.py
```

### Automated Execution

GitHub Actions workflow runs automatically:
- **Calendar**: Every hour
- **Metrics**: Every 15 minutes

## Output Files

- `calendar_data.json` - Economic events for next 4 weeks
- `dashboard_data.json` - Current metric values

These files are automatically committed and deployed to the frontend.

## Notification System

### Calendar Notifications

**12-Hour Warning:**
- Triggered 12 hours before event
- Shows forecast, impact level

**Data Release:**
- Triggered when actual vs forecast available
- Shows deviation from forecast

### Metrics Notifications

Threshold-based alerts:
- BTC: 0.5% change
- Stablecoin Market Cap: 0.1% change
- USDT Dominance: 0.5% change
- RWA TVL: 1.0% change
- US 10Y Yield: Any change
- Fed Net Liquidity: Any change

## Data Sources

- **investing.com** - Economic calendar
- **CoinGecko** - Crypto prices
- **DeFiLlama** - Stablecoin & RWA data
- **FRED** - US economic indicators

## License

MIT

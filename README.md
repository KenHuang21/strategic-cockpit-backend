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

### Monthly Catalyst Radar

The Monthly Catalyst Radar tracks upcoming US economic events with automated Telegram notifications.

#### Update Frequency
- **Scraping**: Every hour (at :00 minutes)
- **Data Range**: Rolling 4-week window
- **Notifications**: Event-based (see below)

#### Selection Criteria
Events must meet ALL criteria to be included:
- **Country**: United States only
- **Impact Level**: High or Medium
- **Timeframe**: Within next 28 days

#### Data Source
- **Provider**: [investing.com](https://www.investing.com/economic-calendar/)
- **Method**: Web scraping via POST API
- **Refresh**: Hourly to capture latest forecast updates

#### Notification Triggers

**High Impact Events Only** (Medium impact events are displayed but silent):

1. **12-Hour Warning**
   - Sent once when event is 0-12 hours away
   - Shows: Event name, time, forecast, impact level
   - Duplicate prevention via persistent flags

2. **Data Release**
   - Sent once when actual vs forecast becomes available
   - Shows: Actual value, forecast, deviation percentage
   - Only if actual data differs from forecast

**Example:**
```
⚠️ Upcoming Catalyst (11.5h)

🔴 Existing Home Sales (Nov)
📅 2025-12-19 at 10:00
📊 Forecast: 4.15M
⚡ Impact: High
```

Then at release:
```
📊 Data Released

🔴 Existing Home Sales (Nov)
Actual: 4.20M vs 4.15M forecast
Deviation: +1.2% (beat)
```

#### Display Behavior
- **Frontend**: Shows ALL High + Medium impact events
- **Telegram**: Only High impact events trigger notifications
- **Timeline**: Grouped by week (This Week, Next Week, Week 3, Week 4)

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

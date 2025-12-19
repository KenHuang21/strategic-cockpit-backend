#!/usr/bin/env python3
"""
Macro & Web3 Strategic Dashboard - Metrics Fetcher
Fetches 6 key financial/crypto metrics from multiple data sources.
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, Optional
import yfinance as yf
from fredapi import Fred
from tabulate import tabulate


class MetricsFetcher:
    """Fetches and processes financial metrics from various sources."""
    
    # Notification thresholds for each metric
    NOTIFICATION_THRESHOLDS = {
        'bitcoin_price': 0.5,           # 0.5% change
        'us_10y_yield': 0.0,            # 0.0 = any change triggers alert
        'fed_net_liquidity': 0.0,       # 0.0 = any change triggers alert
        'stablecoin_mcap': 0.1,         # 0.1% change
        'usdt_dominance': 0.5,          # 0.5% change
        'rwa_tvl': 1.0                  # 1.0% change
    }
    
    def __init__(self, fred_api_key: str = "YOUR_FRED_API_KEY"):
        """
        Initialize the metrics fetcher.
        
        Args:
            fred_api_key: API key for FRED (Federal Reserve Economic Data)
        """
        self.fred_api_key = fred_api_key
        self.results = []
        self.data = {}
        self.metric_changes = {}  # Store percentage changes for notifications
        
        # Create a custom session for yfinance with User-Agent headers
        self.yf_session = requests.Session()
        self.yf_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
    def fetch_us_10y_yield(self) -> Optional[float]:
        """
        Fetch US 10-Year Treasury Bond Yield.
        Primary: FRED API (DGS10)
        Fallback: yfinance with custom session
        
        Returns:
            Current yield value or None if fetch fails
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Method 1 (Primary): Try FRED API first
                if self.fred_api_key != "YOUR_FRED_API_KEY":
                    try:
                        from datetime import datetime, timedelta
                        fred = Fred(api_key=self.fred_api_key)
                        
                        # Get last 14 days of data to ensure we have 7 business days
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=14)
                        
                        dgs10 = fred.get_series('DGS10', start_date=start_date, end_date=end_date)
                        
                        # Current value (most recent)
                        value = float(dgs10.iloc[-1])
                        
                        # Calculate 7-day change
                        seven_day_change = None
                        if len(dgs10) >= 7:
                            # Get value from ~7 business days ago
                            old_value = float(dgs10.iloc[-7])
                            seven_day_change = ((value - old_value) / old_value) * 100
                        
                        self.results.append({
                            "Metric": "US 10Y Bond Yield",
                            "Value": f"{value:.2f}%",
                            "Source": "FRED API (DGS10)",
                            "Status": "✓ Success"
                        })
                        self.data["us_10y_yield"] = value
                        if seven_day_change is not None:
                            self.data["us_10y_yield_7d_change"] = seven_day_change
                        return value
                    except Exception:
                        pass  # If FRED fails, try yfinance
                
                # Method 2 (Fallback): Try yfinance with custom session
                try:
                    ticker = yf.Ticker("^TNX", session=self.yf_session)
                    hist = ticker.history(period="5d")
                    
                    if not hist.empty:
                        value = float(hist['Close'].iloc[-1])
                        self.results.append({
                            "Metric": "US 10Y Bond Yield",
                            "Value": f"{value:.2f}%",
                            "Source": "yfinance (^TNX)",
                            "Status": "✓ Success"
                        })
                        self.data["us_10y_yield"] = value
                        return value
                except Exception:
                    pass  # Both failed
                
                raise ValueError("Both FRED and yfinance failed")
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait 2 seconds before retry
                    continue
                else:
                    self.results.append({
                        "Metric": "US 10Y Bond Yield",
                        "Value": "N/A",
                        "Source": "FRED/yfinance",
                        "Status": f"✗ Failed: {str(e)[:30]}"
                    })
                    self.data["us_10y_yield"] = None
                    return None
    
    def fetch_bitcoin_price(self) -> Optional[float]:
        """
        Fetch current Bitcoin price.
        Primary: CoinGecko API
        Fallback: yfinance with custom session
        
        Returns:
            Current BTC price in USD or None if fetch fails
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Method 1 (Primary): Try CoinGecko first
                try:
                    btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
                    response = requests.get(btc_url, timeout=10)
                    response.raise_for_status()
                    btc_data = response.json()
                    value = float(btc_data['bitcoin']['usd'])
                    self.results.append({
                        "Metric": "Bitcoin Price",
                        "Value": f"${value:,.2f}",
                        "Source": "CoinGecko API",
                        "Status": "✓ Success"
                    })
                    self.data["bitcoin_price"] = value
                    return value
                except Exception:
                    pass  # If CoinGecko fails, try yfinance
                
                # Method 2 (Fallback): Try yfinance with custom session
                try:
                    ticker = yf.Ticker("BTC-USD", session=self.yf_session)
                    hist = ticker.history(period="5d")
                    
                    if not hist.empty:
                        value = float(hist['Close'].iloc[-1])
                        self.results.append({
                            "Metric": "Bitcoin Price",
                            "Value": f"${value:,.2f}",
                            "Source": "yfinance (BTC-USD)",
                            "Status": "✓ Success"
                        })
                        self.data["bitcoin_price"] = value
                        return value
                except Exception:
                    pass  # Both failed
                
                raise ValueError("Both CoinGecko and yfinance failed")
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait 2 seconds before retry
                    continue
                else:
                    self.results.append({
                        "Metric": "Bitcoin Price",
                        "Value": "N/A",
                        "Source": "CoinGecko/yfinance",
                        "Status": f"✗ Failed: {str(e)[:30]}"
                    })
                    self.data["bitcoin_price"] = None
                    return None
    
    def fetch_stablecoin_mcap(self) -> Optional[float]:
        """
        Fetch total Stablecoin Market Cap from DefiLlama.
        
        Returns:
            Total stablecoin market cap or None if fetch fails
        """
        try:
            url = "https://stablecoins.llama.fi/stablecoins?includePrices=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Sum circulating USD for all stablecoins
            total_mcap = 0
            for coin in data.get('peggedAssets', []):
                circulating = coin.get('circulating', {}).get('peggedUSD', 0)
                if circulating:
                    total_mcap += float(circulating)
            
            if total_mcap == 0:
                raise ValueError("No stablecoin data found")
                
            value = total_mcap
            self.results.append({
                "Metric": "Stablecoin Market Cap",
                "Value": f"${value:,.0f}",
                "Source": "DefiLlama API",
                "Status": "✓ Success"
            })
            self.data["stablecoin_mcap"] = value
            return value
            
        except Exception as e:
            self.results.append({
                "Metric": "Stablecoin Market Cap",
                "Value": "N/A",
                "Source": "DefiLlama API",
                "Status": f"✗ Failed: {str(e)[:30]}"
            })
            self.data["stablecoin_mcap"] = None
            return None
    
    def fetch_rwa_tvl(self) -> Optional[float]:
        """
        Fetch Total RWA (Real World Assets) TVL from DefiLlama.
        
        Returns:
            Total RWA TVL or None if fetch fails
        """
        try:
            # Fetch all protocols from DefiLlama
            url = "https://api.llama.fi/protocols"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            protocols = response.json()
            
            # Filter protocols by RWA category and sum their TVL
            target_categories = ["RWA", "RWA Lending", "Private Credit", "Real World Assets"]
            total_rwa_tvl = 0
            rwa_count = 0
            
            for protocol in protocols:
                # Check if protocol is in target categories
                if protocol.get('category') in target_categories:
                    tvl = protocol.get('tvl', 0)
                    if tvl:
                        total_rwa_tvl += float(tvl)
                        rwa_count += 1
            
            if total_rwa_tvl == 0:
                raise ValueError("No RWA protocols found or total TVL is zero")
            
            value = total_rwa_tvl
            self.results.append({
                "Metric": "Total RWA TVL",
                "Value": f"${value:,.0f}",
                "Source": f"DefiLlama API ({rwa_count} protocols)",
                "Status": "✓ Success"
            })
            self.data["rwa_tvl"] = value
            return value
            
        except Exception as e:
            self.results.append({
                "Metric": "Total RWA TVL",
                "Value": "N/A",
                "Source": "DefiLlama API",
                "Status": f"✗ Failed: {str(e)[:30]}"
            })
            self.data["rwa_tvl"] = None
            return None
    
    def fetch_usdt_dominance(self) -> Optional[float]:
        """
        Fetch USDT Dominance (USDT Market Cap / Total Crypto Market Cap * 100).
        Uses CoinGecko API for market cap data.
        
        Returns:
            USDT dominance percentage or None if fetch fails
        """
        try:
            # Fetch USDT market cap
            usdt_url = "https://api.coingecko.com/api/v3/coins/tether"
            response = requests.get(usdt_url, timeout=10)
            response.raise_for_status()
            usdt_data = response.json()
            usdt_mcap = float(usdt_data['market_data']['market_cap']['usd'])
            
            # Fetch global crypto market cap
            global_url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(global_url, timeout=10)
            response.raise_for_status()
            global_data = response.json()
            total_mcap = float(global_data['data']['total_market_cap']['usd'])
            
            # Calculate dominance
            dominance = (usdt_mcap / total_mcap) * 100
            
            self.results.append({
                "Metric": "USDT Dominance",
                "Value": f"{dominance:.2f}%",
                "Source": "CoinGecko API",
                "Status": "✓ Success"
            })
            self.data["usdt_dominance"] = dominance
            return dominance
            
        except Exception as e:
            self.results.append({
                "Metric": "USDT Dominance",
                "Value": "N/A",
                "Source": "CoinGecko API",
                "Status": f"✗ Failed: {str(e)[:30]}"
            })
            self.data["usdt_dominance"] = None
            return None
    
    def fetch_fed_net_liquidity(self) -> Optional[float]:
        """
        Fetch Fed Net Liquidity.
        Formula: WALCL (Total Assets) - TGA (Treasury General Account) - RRP (Reverse Repo)
        
        Returns:
            Net liquidity value or None if fetch fails
        """
        try:
            if self.fred_api_key == "YOUR_FRED_API_KEY":
                raise ValueError("FRED API key not configured")
                
            from datetime import datetime, timedelta
            fred = Fred(api_key=self.fred_api_key)
            
            # Get last 14 days of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=14)
            
            # Fetch the latest values for each series
            walcl_series = fred.get_series('WALCL', start_date=start_date, end_date=end_date)
            tga_series = fred.get_series('WTREGEN', start_date=start_date, end_date=end_date)
            rrp_series = fred.get_series('RRPONTSYD', start_date=start_date, end_date=end_date)
            
            # Current values
            walcl = walcl_series.iloc[-1]
            tga = tga_series.iloc[-1]
            rrp = rrp_series.iloc[-1]
            
            # Calculate current net liquidity (in billions)
            net_liquidity = float(walcl - tga - rrp)
            
            # Calculate 7-day change
            seven_day_change = None
            if len(walcl_series) >= 7 and len(tga_series) >= 7 and len(rrp_series) >= 7:
                old_walcl = walcl_series.iloc[-7]
                old_tga = tga_series.iloc[-7]
                old_rrp = rrp_series.iloc[-7]
                old_net_liquidity = float(old_walcl - old_tga - old_rrp)
                seven_day_change = ((net_liquidity - old_net_liquidity) / old_net_liquidity) * 100
            
            self.results.append({
                "Metric": "Fed Net Liquidity",
                "Value": f"${net_liquidity:,.0f}B",
                "Source": "FRED API",
                "Status": "✓ Success"
            })
            self.data["fed_net_liquidity"] = net_liquidity
            if seven_day_change is not None:
                self.data["fed_net_liquidity_7d_change"] = seven_day_change
            return net_liquidity
            
        except Exception as e:
            self.results.append({
                "Metric": "Fed Net Liquidity",
                "Value": "N/A",
                "Source": "FRED API",
                "Status": f"✗ Failed: {str(e)[:30]}"
            })
            self.data["fed_net_liquidity"] = None
            return None
    
    def fetch_all_metrics(self) -> Dict[str, Any]:
        """
        Fetch all 6 metrics and compile results.
        
        Returns:
            Dictionary containing all metrics and metadata
        """
        print("🔄 Fetching Macro & Web3 Metrics...\n")
        
        # Fetch all metrics
        self.fetch_us_10y_yield()
        self.fetch_bitcoin_price()
        self.fetch_stablecoin_mcap()
        self.fetch_rwa_tvl()
        self.fetch_usdt_dominance()
        self.fetch_fed_net_liquidity()
        
        # Print results table
        print("\n" + "="*80)
        print("📊 MACRO & WEB3 STRATEGIC DASHBOARD - METRICS REPORT")
        print("="*80 + "\n")
        print(tabulate(self.results, headers="keys", tablefmt="rounded_grid"))
        print("\n" + "="*80 + "\n")
        
        # Compile final output
        output = {
            "timestamp": datetime.utcnow().isoformat() + "Z",  # Explicitly mark as UTC
            "timestamp_unix": int(datetime.utcnow().timestamp()),
            "metrics": self.data,
            "summary": {
                "total_metrics": len(self.results),
                "successful": len([r for r in self.results if "✓" in r["Status"]]),
                "failed": len([r for r in self.results if "✗" in r["Status"]])
            }
        }
        
        return output
    
    def save_to_json(self, output: Dict[str, Any], filename: str = "dashboard_data.json"):
        """
        Save metrics data to JSON file.
        
        Args:
            output: Data dictionary to save
            filename: Output filename
        """
        try:
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"✅ Data saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")
    
    def load_old_data(self, filename: str = "dashboard_data.json") -> Optional[Dict[str, Any]]:
        """
        Load previous metrics data from JSON file.
        
        Args:
            filename: JSON filename to load
            
        Returns:
            Previous data dictionary or None if file doesn't exist
        """
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("ℹ️  No previous data found (first run)")
            return None
        except Exception as e:
            print(f"⚠️  Failed to load old data: {e}")
            return None
    
    def check_metrics_changed(self, new_data: Dict[str, Any], old_data: Optional[Dict[str, Any]]) -> tuple[bool, list]:
        """
        Check if any of the 6 strategic metrics have changed beyond their thresholds.
        
        Args:
            new_data: Newly fetched metrics
            old_data: Previous metrics data
            
        Returns:
            Tuple of (should_notify: bool, changed_metrics: list)
        """
        # The 6 metrics to track
        tracked_metrics = [
            'us_10y_yield',
            'fed_net_liquidity',
            'bitcoin_price',
            'stablecoin_mcap',
            'usdt_dominance',
            'rwa_tvl'
        ]
        
        # Metrics that use absolute threshold instead of percentage
        absolute_threshold_metrics = ['us_10y_yield']
        
        # If no old data exists (first run), notify
        if old_data is None:
            return True, tracked_metrics
        
        changed_metrics = []
        old_metrics = old_data.get('metrics', {})
        new_metrics = new_data.get('metrics', {})
        self.metric_changes = {}  # Reset changes dictionary
        
        # Check each metric for threshold-based changes
        for metric in tracked_metrics:
            old_value = old_metrics.get(metric)
            new_value = new_metrics.get(metric)
            
            # Skip if either value is None
            if old_value is None or new_value is None:
                if old_value != new_value:
                    changed_metrics.append(metric)
                continue
            
            # Skip if values are exactly equal (no change at all)
            if old_value == new_value:
                continue
            
            # Get threshold for this metric
            threshold = self.NOTIFICATION_THRESHOLDS.get(metric, 0)
            
            # Calculate change based on metric type
            if metric in absolute_threshold_metrics:
                # Absolute change (e.g., yield 4.15% -> 4.20% = 0.05 change)
                absolute_change = abs(new_value - old_value)
                exceeds_threshold = absolute_change >= threshold
                pct_change = ((new_value - old_value) / old_value) * 100 if old_value != 0 else 0
            else:
                # Percentage change
                pct_change = ((new_value - old_value) / old_value) * 100 if old_value != 0 else 0
                exceeds_threshold = abs(pct_change) >= threshold
            
            # Mark as changed if threshold exceeded
            if exceeds_threshold:
                # Store the change for notification formatting (ONLY if threshold exceeded)
                self.metric_changes[metric] = {
                    'old': old_value,
                    'new': new_value,
                    'pct_change': pct_change,
                    'direction': '▲' if new_value > old_value else '▼'
                }
                changed_metrics.append(metric)
        
        should_notify = len(changed_metrics) > 0
        return should_notify, changed_metrics
    
    def format_telegram_message(self, data: Dict[str, Any]) -> str:
        """
        Format metrics data into HTML message for Telegram with delta indicators.
        
        Args:
            data: Metrics data dictionary
            
        Returns:
            Formatted HTML string
        """
        metrics = data.get('metrics', {})
        
        # Extract values with fallbacks
        us_10y = metrics.get('us_10y_yield', 'N/A')
        fed_liquidity = metrics.get('fed_net_liquidity', 'N/A')
        btc_price = metrics.get('bitcoin_price', 'N/A')
        stablecoin_mcap = metrics.get('stablecoin_mcap', 'N/A')
        usdt_dominance = metrics.get('usdt_dominance', 'N/A')
        rwa_value = metrics.get('rwa_tvl', 'N/A')
        
        # Helper function to format metric with delta
        def format_with_delta(value, metric_key, value_formatter):
            if not isinstance(value, (int, float)):
                return str(value)
            
            formatted_value = value_formatter(value)
            
            # Add delta if available
            if metric_key in self.metric_changes:
                change = self.metric_changes[metric_key]
                direction = change['direction']
                pct_change = change['pct_change']
                
                # Color code: green for up, red for down
                color = '#00ff00' if direction == '▲' else '#ff0000'
                delta_str = f"<span style='color:{color};'>{direction} {abs(pct_change):.2f}%</span>"
                return f"{formatted_value} {delta_str}"
            
            return formatted_value
        
        # Format numbers with deltas
        us_10y_str = format_with_delta(us_10y, 'us_10y_yield', lambda v: f"{v:.2f}")
        fed_liquidity_str = format_with_delta(fed_liquidity, 'fed_net_liquidity', lambda v: f"{v:,.0f}B")
        btc_price_str = format_with_delta(btc_price, 'bitcoin_price', lambda v: f"{v:,.0f}")
        stablecoin_mcap_str = format_with_delta(stablecoin_mcap, 'stablecoin_mcap', lambda v: f"{v/1e9:.1f}B")
        usdt_dominance_str = format_with_delta(usdt_dominance, 'usdt_dominance', lambda v: f"{v:.2f}")
        rwa_value_str = format_with_delta(rwa_value, 'rwa_tvl', lambda v: f"{v/1e9:.2f}B")
        
        # Determine risk status
        risk_status = "⚠️ RISK OFF" if isinstance(us_10y, (int, float)) and us_10y > 4.5 else "✅ RISK ON"
        
        # Build message
        message = f"""<b>🚨 Strategic Cockpit Update</b>

<b>Macro (The Ceiling)</b>
🏛️ <b>US 10Y:</b> {us_10y_str}%
💧 <b>Liquidity:</b> ${fed_liquidity_str}

<b>Market (The Floor)</b>
₿ <b>BTC:</b> ${btc_price_str}
🌊 <b>Stablecoins:</b> ${stablecoin_mcap_str}

<b>Alpha Signals</b>
😨 <b>USDT Dom:</b> {usdt_dominance_str}%
🏦 <b>RWA TVL:</b> ${rwa_value_str}

<b>Status:</b> {risk_status}"""
        
        return message
    
    def send_telegram_notification(self, message: str, telegram_bot_token: str, telegram_chat_id: str) -> bool:
        """
        Send notification to Telegram.
        
        Args:
            message: Message text to send (HTML formatted)
            telegram_bot_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not telegram_bot_token or not telegram_chat_id:
            print("⚠️  Telegram credentials not configured. Skipping notification.")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            print("✅ Telegram notification sent successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send Telegram notification: {e}")
            return False


def main():
    """Main execution function."""
    import os
    
    # Get credentials from environment variables
    fred_api_key = os.getenv('FRED_API_KEY', '1be1d07bd97df586c3e81893338b87dc')
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Initialize fetcher
    fetcher = MetricsFetcher(fred_api_key=fred_api_key)
    
    # Load old data for comparison
    old_data = fetcher.load_old_data()
    
    # Fetch all metrics
    new_data = fetcher.fetch_all_metrics()
    
    # Check if any metrics changed
    should_notify, changed_metrics = fetcher.check_metrics_changed(new_data, old_data)
    
    if should_notify:
        print(f"\n📊 Metrics changed: {', '.join(changed_metrics)}")
        
        # Format and send Telegram notification
        message = fetcher.format_telegram_message(new_data)
        fetcher.send_telegram_notification(message, telegram_bot_token, telegram_chat_id)
    else:
        print("\nℹ️  No metrics changed since last update")
    
    # Save to JSON (always save to update timestamp)
    fetcher.save_to_json(new_data)


if __name__ == "__main__":
    main()

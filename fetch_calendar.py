#!/usr/bin/env python3
"""
Monthly Catalyst Radar - Economic Calendar Fetcher
Scrapes US economic events from investing.com with dual-trigger notifications.
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import cloudscraper
from bs4 import BeautifulSoup


class EconomicCalendarFetcher:
    """Fetches and processes economic calendar data from investing.com."""
    
    def __init__(self, telegram_bot_token: str = "", telegram_chat_id: str = ""):
        """
        Initialize the calendar fetcher.
        
        Args:
            telegram_bot_token: Telegram bot token for notifications
            telegram_chat_id: Telegram chat ID for notifications
        """
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
    def generate_event_id(self, date: str, name: str) -> str:
        """
        Generate unique event ID from date and name.
        
        Args:
            date: Event date (YYYY-MM-DD)
            name: Event name
            
        Returns:
            Unique hash string
        """
        unique_str = f"{date}_{name}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    
    def load_existing_data(self, filename: str = "calendar_data.json") -> Dict[str, Any]:
        """
        Load existing calendar data to preserve notification flags.
        
        Args:
            filename: JSON filename
            
        Returns:
            Existing data dictionary or empty structure
        """
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("ℹ️  No existing calendar data found (first run)")
            return {"updated_at": None, "events": []}
        except Exception as e:
            print(f"⚠️  Failed to load existing data: {e}")
            return {"updated_at": None, "events": []}
    
    def fetch_calendar_events(self) -> List[Dict[str, Any]]:
        """
        Scrape economic calendar from investing.com.
        
        Returns:
            List of event dictionaries
        """
        events = []
        
        # Calculate date range (today + 28 days)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=28)
        
        print(f"🔄 Fetching economic calendar from {start_date.date()} to {end_date.date()}...")
        
        try:
            # Investing.com AJAX endpoint for custom date ranges
            url = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
            
            # Format dates as YYYY-MM-DD
            date_from = start_date.strftime('%Y-%m-%d')
            date_to = end_date.strftime('%Y-%m-%d')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://www.investing.com',
                'Referer': 'https://www.investing.com/economic-calendar/'
            }
            
            # POST data for custom date range
            data = {
                'dateFrom': date_from,
                'dateTo': date_to,
                'currentTab': 'custom',
                'limit_from': '0',
                'timeZone': '8'  # GMT+8 (Singapore/Asia timezone)
            }
            
            print(f"Fetching calendar data: {date_from} to {date_to}")
            
            response = self.scraper.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            # The AJAX endpoint returns JSON with HTML in the 'data' field
            try:
                json_response = response.json()
                html_data = json_response.get('data', '')
                if not html_data:
                    print("❌ No data in AJAX response")
                    return []
            except Exception as e:
                print(f"❌ Failed to parse JSON response: {e}")
                # Fallback: try parsing as HTML directly
                html_data = response.text
            
            soup = BeautifulSoup(html_data, 'lxml')
            
            # Parse event rows (tr.js-event-item excludes date header rows)
            event_rows = soup.find_all('tr', {'class': 'js-event-item'})
            
            print(f"Found {len(event_rows)} total events")
            
            for row in event_rows:
                try:
                    # Get datetime from data attribute (most reliable)
                    event_datetime_str = row.get('data-event-datetime', '')
                    if not event_datetime_str:
                        continue
                    
                    # Parse datetime (format: YYYY/MM/DD HH:mm:ss)
                    try:
                        event_datetime = datetime.strptime(event_datetime_str, '%Y/%m/%d %H:%M:%S')
                    except ValueError:
                        print(f"⚠️  Could not parse datetime: {event_datetime_str}")
                        continue
                    
                    # Filter: Only events within our 28-day window
                    if event_datetime < start_date or event_datetime > end_date:
                        continue
                    
                    # Get currency/country
                    currency_elem = row.find('td', {'class': 'flagCur'})
                    if not currency_elem:
                        continue
                    
                    currency = currency_elem.get_text(strip=True)
                    
                    # Filter: US events only (currency = USD)
                    if currency != 'USD':
                        continue
                    
                    # Get importance/impact
                    impact_elem = row.find('td', {'class': 'sentiment'})
                    if not impact_elem:
                        continue
                    
                    # Check data-img_key attribute (bull1, bull2, bull3)
                    img_key = impact_elem.get('data-img_key', '')
                    
                    # Filter: High (bull3) or Medium (bull2) impact only
                    if img_key not in ['bull2', 'bull3']:
                        continue
                    
                    impact = "High" if img_key == 'bull3' else "Medium"
                    
                    # Get event name
                    name_elem = row.find('td', {'class': 'event'})
                    name = name_elem.get_text(strip=True) if name_elem else "Unknown Event"
                    
                    # Clean up name (remove extra whitespace)
                    name = ' '.join(name.split())
                    
                    # Get time (visible time text)
                    time_elem = row.find('td', {'class': 'time'})
                    event_time = time_elem.get_text(strip=True) if time_elem else event_datetime.strftime('%H:%M')
                    
                    # Get forecast value
                    forecast_elem = row.find('td', {'class': 'fore'})
                    forecast = forecast_elem.get_text(strip=True) if forecast_elem else None
                    if forecast == '' or forecast == '\xa0':
                        forecast = None
                    
                    # Get actual value
                    actual_elem = row.find('td', {'class': 'act'})
                    actual = actual_elem.get_text(strip=True) if actual_elem else None
                    if actual == '' or actual == '\xa0':
                        actual = None
                    
                    # Get previous value
                    prev_elem = row.find('td', {'class': 'prev'})
                    previous = prev_elem.get_text(strip=True) if prev_elem else None
                    if previous == '' or previous == '\xa0':
                        previous = None
                    
                    # Determine status
                    status = "completed" if actual else "upcoming"
                    
                    # Format date as YYYY-MM-DD
                    event_date = event_datetime.strftime('%Y-%m-%d')
                    
                    event = {
                        "id": self.generate_event_id(event_date, name),
                        "date": event_date,
                        "time": event_time,
                        "name": name,
                        "impact": impact,
                        "forecast": forecast,
                        "actual": actual,
                        "previous": previous,
                        "status": status,
                        "notification_sent_12h": False,
                        "notification_sent_release": False
                    }
                    
                    events.append(event)
                    
                except Exception as e:
                    print(f"⚠️  Failed to parse event row: {e}")
                    continue
            
            print(f"✅ Scraped {len(events)} US High/Medium impact events")
            return events
            
        except Exception as e:
            print(f"❌ Failed to fetch calendar: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def merge_with_existing(self, new_events: List[Dict], old_data: Dict) -> List[Dict]:
        """
        Merge new events with existing data, preserving notification flags.
        
        Args:
            new_events: Newly scraped events
            old_data: Existing calendar data
            
        Returns:
            Merged event list
        """
        # Create lookup for old events
        old_events_map = {event['id']: event for event in old_data.get('events', [])}
        
        merged_events = []
        for new_event in new_events:
            event_id = new_event['id']
            
            if event_id in old_events_map:
                old_event = old_events_map[event_id]
                # Preserve notification flags
                new_event['notification_sent_12h'] = old_event.get('notification_sent_12h', False)
                new_event['notification_sent_release'] = old_event.get('notification_sent_release', False)
                
                # Update actual value if it changed
                if new_event['actual'] and not old_event.get('actual'):
                    new_event['status'] = 'completed'
            
            merged_events.append(new_event)
        
        return merged_events
    
    def check_and_send_notifications(self, events: List[Dict]) -> List[Dict]:
        """
        Check events and send notifications based on triggers.
        
        Args:
            events: List of events to check
            
        Returns:
            Updated events list with notification flags
        """
        now = datetime.now()
        updated_events = []
        
        for event in events:
            try:
                # Parse event datetime
                event_datetime_str = f"{event['date']} {event['time']}"
                # This needs proper parsing based on actual format
                # For now, using a placeholder
                event_datetime = datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M")
                
                time_until_event = event_datetime - now
                hours_until = time_until_event.total_seconds() / 3600
                
                # Trigger A: 12-hour warning (ONLY for High impact events)
                if (0 <= hours_until <= 12 and 
                    not event['notification_sent_12h'] and 
                    event['impact'] == 'High'):  # Only High impact
                    message = self.format_warning_message(event, hours_until)
                    if self.send_telegram_notification(message):
                        event['notification_sent_12h'] = True
                        print(f"📢 Sent 12h warning for: {event['name']}")
                
                
                # Trigger B: Data release (ONLY for High impact events)
                if (event['status'] == 'completed' and 
                    event['actual'] and 
                    not event['notification_sent_release'] and
                    event['impact'] == 'High'):  # Only High impact
                    message = self.format_release_message(event)
                    if self.send_telegram_notification(message):
                        event['notification_sent_release'] = True
                        print(f"📢 Sent release notification for: {event['name']}")
                
                updated_events.append(event)
                
            except Exception as e:
                print(f"⚠️  Error processing event {event.get('name', 'Unknown')}: {e}")
                updated_events.append(event)
        
        return updated_events
    
    def format_warning_message(self, event: Dict, hours_until: float) -> str:
        """Format 12-hour warning message."""
        impact_emoji = "🔴" if event['impact'] == "High" else "🟡"
        hours_str = f"{hours_until:.1f}h"
        
        message = f"""⚠️ <b>Upcoming Catalyst ({hours_str})</b>

{impact_emoji} <b>{event['name']}</b>
📅 {event['date']} at {event['time']}
📊 Forecast: <b>{event['forecast'] or 'N/A'}</b>
⚡ Impact: <b>{event['impact']}</b>"""
        
        return message
    
    def format_release_message(self, event: Dict) -> str:
        """Format data release message with actual vs forecast."""
        impact_emoji = "🔴" if event['impact'] == "High" else "🟡"
        
        # Calculate deviation
        deviation_text = ""
        if event['forecast'] and event['actual']:
            try:
                # Simple numeric comparison (may need more sophisticated parsing)
                forecast_val = float(event['forecast'].replace('K', '000').replace('%', ''))
                actual_val = float(event['actual'].replace('K', '000').replace('%', ''))
                deviation = actual_val - forecast_val
                pct_deviation = (deviation / forecast_val * 100) if forecast_val != 0 else 0
                
                deviation_emoji = "🟢" if deviation > 0 else "🔴"
                deviation_text = f"\n{deviation_emoji} Deviation: {deviation:+.1f} ({pct_deviation:+.1f}%)"
            except:
                pass
        
        message = f"""📢 <b>Data Release</b>

{impact_emoji} <b>{event['name']}</b>
📊 Actual: <b>{event['actual']}</b>
🎯 Forecast: {event['forecast'] or 'N/A'}
📍 Previous: {event['previous'] or 'N/A'}{deviation_text}

⏰ Released: {event['date']} {event['time']}"""
        
        return message
    
    def send_telegram_notification(self, message: str) -> bool:
        """Send notification to Telegram."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            print("⚠️  Telegram credentials not configured. Skipping notification.")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"❌ Failed to send Telegram notification: {e}")
            return False
    
    def save_calendar_data(self, events: List[Dict], filename: str = "calendar_data.json"):
        """Save calendar data to JSON file."""
        output = {
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "events": events
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"✅ Calendar data saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save calendar data: {e}")


def main():
    """Main execution function."""
    import os
    
    # Get credentials from environment variables
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Initialize fetcher
    fetcher = EconomicCalendarFetcher(
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id
    )
    
    # Load existing data
    old_data = fetcher.load_existing_data()
    
    # Fetch new events
    new_events = fetcher.fetch_calendar_events()
    
    if not new_events:
        print("⚠️  No events fetched. Using existing data.")
        return
    
    # Merge with existing data
    merged_events = fetcher.merge_with_existing(new_events, old_data)
    
    # Check and send notifications
    updated_events = fetcher.check_and_send_notifications(merged_events)
    
    # Save updated data
    fetcher.save_calendar_data(updated_events)
    
    print(f"\n📊 Summary: {len(updated_events)} events tracked")


if __name__ == "__main__":
    main()

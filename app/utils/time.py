from datetime import datetime, timezone, timedelta

def convert_utc_to_wib(utc_time):
    """Convert UTC timestamp to Indonesia time (WIB/UTC+7)"""
    # check if the input is None or empty
    if not utc_time:
        return None
        
    # Parse the ISO string to datetime 
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time.replace('Z', '+00:00'))
        
    # Convert to Indonesia timezone (UTC+7)
    wib_time = utc_time + timedelta(hours=7)
    # adjut for timezone offset
    wib_time = wib_time.replace(tzinfo=timezone(timedelta(hours=7)))
    return wib_time

def get_wib_day_range():
    """Get today's start and end time in UTC based on Indonesia's time zone"""
    now_utc = datetime.now(timezone.utc)
    now_wib = now_utc + timedelta(hours=7)
    
    wib_today_start = now_wib.replace(hour=0, minute=0, second=0, microsecond=0)
    wib_today_end = wib_today_start + timedelta(days=1) - timedelta(microseconds=1)
    
    today_start_utc = wib_today_start - timedelta(hours=7)
    today_end_utc = wib_today_end - timedelta(hours=7)
    
    return today_start_utc, today_end_utc
from datetime import datetime, timezone, timedelta
import ntplib
import logging
import os
from dotenv import load_dotenv
import time

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default NTP server
NTP_SERVER = os.getenv("NTP_SERVER", "time.nist.gov")

_ntp_offset = 0.0
_last_sync = 0


# NTP use in MQTT
def sync_ntp_time():
    """Synchronize with NTP server and calculate offset"""
    global _ntp_offset, _last_sync
    current_time = time.time()

    # Only sync if more than 15 minutes have passed
    if current_time - _last_sync > 900:  # 15 minutes in seconds
        try:
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request(NTP_SERVER, timeout=5)
            _ntp_offset = response.offset
            _last_sync = current_time
            logger.debug(f"NTP synchronized. Offset: {_ntp_offset:.3f}s")
        except Exception as e:
            logger.error(f"Error synchronizing NTP time: {str(e)}")


def get_accurate_time():
    """Get current time adjusted with NTP offset"""
    sync_ntp_time()  # Will only sync if needed
    return datetime.fromtimestamp(time.time() + _ntp_offset, timezone.utc)


def get_ntp_time():
    """Get current time from NTP server"""
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request(NTP_SERVER, timeout=5)
        ntp_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
        logger.debug(f"NTP time retrieved from {NTP_SERVER}: {ntp_time.isoformat()}")
        return ntp_time
    except Exception as e:
        logger.error(f"Error getting NTP time: {str(e)}. Falling back to system time.")
        return datetime.now(timezone.utc)


def convert_utc_to_wib(utc_time):
    """Convert UTC timestamp to Indonesia time (WIB/UTC+7)"""
    # check if the input is None or empty
    if not utc_time:
        return None

    # Parse the ISO string to datetime
    if isinstance(utc_time, str):
        utc_time = datetime.fromisoformat(utc_time.replace("Z", "+00:00"))

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

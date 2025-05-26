import sqlite3
import os
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Create database directory if it doesn't exist
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "mqtt_data.db"

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with required tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create table for MQTT GPS data
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mqtt_gps_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracker_id TEXT NOT NULL,
            latitude REAL NULL,
            longitude REAL NULL,
            receive_time DATETIME NOT NULL,
            send_time DATETIME,
            latency_ms REAL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create index for faster queries by tracker_id
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tracker_id
        ON mqtt_gps_data (tracker_id)
        ''')
        
        # Create index for time-based queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_receive_time
        ON mqtt_gps_data (receive_time)
        ''')
        
        conn.commit()
        logger.info("SQLite database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def store_gps_data(tracker_id, latitude, longitude, receive_time, send_time=None, latency_ms=None):
    """Store GPS data in SQLite database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # logger.debug(f"All Time : {receive_time} - {send_time} = {latency_ms} ms")
        # logger.debug(f"Data type for time : {type(receive_time)} - {type(send_time)}")
        # Convert datetime objects to ISO format strings
        # if isinstance(receive_time, datetime):
        #     receive_time = receive_time.isoformat()
        
        # if isinstance(send_time, datetime):
        #     send_time = send_time.isoformat()
        
        # current_time = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO mqtt_gps_data 
        (tracker_id, latitude, longitude, receive_time, send_time, latency_ms)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            tracker_id, 
            latitude, 
            longitude, 
            receive_time, 
            send_time,
            latency_ms
            # current_time
        ))
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error storing GPS data in SQLite: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def get_recent_gps_data(trackerId=None, limit=100):
    """Get recent GPS data from SQLite database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if trackerId:
            cursor.execute('''
            SELECT * FROM mqtt_gps_data 
            WHERE tracker_id = ? 
            ORDER BY id DESC LIMIT ?
            ''', (trackerId, limit))
        else:
            cursor.execute('''
            SELECT * FROM mqtt_gps_data 
            ORDER BY id DESC LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        # return [dict(row) for row in rows]
        # Convert datetime strings back to datetime objects
        result = []
        for row in rows:
            row_dict = dict(row)
            # SQLite returns datetime as string, convert back to datetime objects
            for field in ['receive_time', 'send_time', 'created_at']:
                if row_dict.get(field):
                    try:
                        # Handle both formats: with and without 'Z' suffix
                        time_str = row_dict[field]
                        if time_str.endswith('Z'):
                            row_dict[field] = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        elif '+' in time_str or time_str.endswith('UTC'):
                            row_dict[field] = datetime.fromisoformat(time_str)
                        else:
                            # Assume UTC if no timezone info
                            row_dict[field] = datetime.fromisoformat(time_str).replace(tzinfo=timezone.utc)
                    except ValueError:
                        # Keep as string if conversion fails
                        pass
            result.append(row_dict)
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving GPS data from SQLite: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

# Initialize the database when the module is imported
init_db()
import sqlite3
import os
import logging
from datetime import datetime
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
            receive_time TEXT NOT NULL,
            send_time TEXT,
            latency_ms REAL,
            created_at TEXT NOT NULL
        )
        ''')
        
        # Create index for faster queries by tracker_id
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tracker_id
        ON mqtt_gps_data (tracker_id)
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
        
        # Convert datetime objects to ISO format strings
        if isinstance(receive_time, datetime):
            receive_time = receive_time.isoformat()
        
        if isinstance(send_time, datetime):
            send_time = send_time.isoformat()
        
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
        INSERT INTO mqtt_gps_data 
        (tracker_id, latitude, longitude, receive_time, send_time, latency_ms, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            tracker_id, 
            latitude, 
            longitude, 
            receive_time, 
            send_time,
            latency_ms,
            current_time
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
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error retrieving GPS data from SQLite: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

# Initialize the database when the module is imported
init_db()
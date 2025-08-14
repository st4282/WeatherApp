import sqlite3
from datetime import datetime

DATABASE_NAME = 'weather_queries.db'

def init_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            location_type TEXT NOT NULL,
            location TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            temp REAL,
            temp_min REAL,
            temp_max REAL,
            feels_like REAL,
            description TEXT,
            local_time TEXT,
            weather_icon TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_connection():
    return sqlite3.connect(DATABASE_NAME)

def create_weather_record(label, location_type, location, start_date, end_date, weather_data):
    conn = get_connection()
    cursor = conn.cursor()
    
    current_time = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO weather_records 
        (label, location_type, location, start_date, end_date, temp, temp_min, temp_max, 
         feels_like, description, local_time, weather_icon, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        label,
        location_type,
        location,
        start_date,
        end_date,
        weather_data.get('temp'),
        weather_data.get('temp_min'),
        weather_data.get('temp_max'),
        weather_data.get('feels_like'),
        weather_data.get('description'),
        weather_data.get('local_time'),
        weather_data.get('weather_icon'),
        current_time,
        current_time
    ))

    record_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return record_id

def read_all_records():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, label, location_type, location, start_date, end_date, 
               temp, temp_min, temp_max, feels_like, description, 
               local_time, weather_icon, created_at, updated_at
        FROM weather_records
        ORDER BY created_at DESC
    ''')
    
    records = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries for easier handling
    columns = ['id', 'label', 'location_type', 'location', 'start_date', 'end_date',
              'temp', 'temp_min', 'temp_max', 'feels_like', 'description',
              'local_time', 'weather_icon', 'created_at', 'updated_at']
    
    return [dict(zip(columns, record)) for record in records]

def update_record_label(record_id, new_label):
    conn = get_connection()
    cursor = conn.cursor()
    
    current_time = datetime.now().isoformat()
    
    cursor.execute('''
        UPDATE weather_records 
        SET label = ?, updated_at = ?
        WHERE id = ?
    ''', (new_label, current_time, record_id))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0

def delete_record(record_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM weather_records WHERE id = ?', (record_id,))
    
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return rows_affected > 0

def get_record_by_id(record_id):
    """Get a specific record by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, label, location_type, location, start_date, end_date, 
               temp, temp_min, temp_max, feels_like, description, 
               local_time, weather_icon, created_at, updated_at
        FROM weather_records
        WHERE id = ?
    ''', (record_id,))
    
    record = cursor.fetchone()
    conn.close()
    
    if record:
        columns = ['id', 'label', 'location_type', 'location', 'start_date', 'end_date',
                  'temp', 'temp_min', 'temp_max', 'feels_like', 'description',
                  'local_time', 'weather_icon', 'created_at', 'updated_at']
        return dict(zip(columns, record))
    
    return None

if __name__ == "__main__":
    init_database()

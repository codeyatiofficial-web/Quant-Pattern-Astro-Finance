import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))
DB_URL = os.getenv("DATABASE_URL", "postgresql://localhost/quant_pattern")

def get_db_connection():
    try:
        return psycopg2.connect(DB_URL)
    except:
        return None

def init_tracker_db():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS magnitude_accuracy (
            id SERIAL PRIMARY KEY,
            signal_timestamp TIMESTAMP,
            predicted_magnitude REAL,
            actual_magnitude REAL,
            prediction_error REAL,
            direction_correct BOOLEAN,
            score_at_signal REAL,
            atr_at_signal REAL,
            global_strength_at_signal REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def log_prediction_result(timestamp, predicted_mag, actual_mag, dir_correct, score, atr, global_str):
    """Log a completed 15m signal's actual vs predicted."""
    conn = get_db_connection()
    if not conn: return
    
    error = abs(actual_mag - predicted_mag)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO magnitude_accuracy 
        (signal_timestamp, predicted_magnitude, actual_magnitude, prediction_error, 
         direction_correct, score_at_signal, atr_at_signal, global_strength_at_signal)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (timestamp, predicted_mag, actual_mag, error, dir_correct, score, atr, global_str))
    
    conn.commit()
    cursor.close()
    conn.close()
    
def generate_weekly_accuracy_report():
    """Calculate MAE, direction accuracy, best score range, and best time of day."""
    conn = get_db_connection()
    if not conn: 
        return {
            "mae": "N/A", "direction_acc": "N/A",
            "best_score_range": "N/A", "best_time": "N/A"
        }
        
    query = '''
        SELECT * FROM magnitude_accuracy 
        WHERE signal_timestamp >= NOW() - INTERVAL '7 days'
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return {
            "mae": "No data", "direction_acc": "No data",
            "best_score_range": "No data", "best_time": "No data"
        }
        
    mae = df['prediction_error'].mean()
    direction_acc = (df['direction_correct'].sum() / len(df)) * 100
    
    # Best score range
    df['score_bucket'] = pd.cut(df['score_at_signal'], bins=[0,60,70,80,90,100], labels=['<60','60-69','70-79','80-89','90-100'])
    bucket_mae = df.groupby('score_bucket')['prediction_error'].mean().dropna()
    best_range = bucket_mae.idxmin() if not bucket_mae.empty else "N/A"
    
    # Best time of day
    df['hour_min'] = pd.to_datetime(df['signal_timestamp']).dt.strftime('%H:%M')
    time_mae = df.groupby('hour_min')['prediction_error'].mean().dropna()
    best_time = time_mae.idxmin() if not time_mae.empty else "N/A"
    
    return {
        "mae": round(mae, 1),
        "direction_acc": round(direction_acc, 1),
        "best_score_range": best_range,
        "best_time": best_time,
        "total_signals": len(df)
    }

if __name__ == "__main__":
    init_tracker_db()
    print("Tracker DB initialized.")
    # Ex: log_prediction_result(datetime.now(), 45.0, 50.0, True, 85.0, 30.5, 1.3)

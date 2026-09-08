"""
MediVision AI - Unified Database Layer (SQLite + Supabase Fallback)
Provides seamless local SQLite database with full query builder compatibility,
and delegates to Supabase when configured.
"""

import os
import sqlite3
import uuid
import json
import bcrypt
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'database', 'medivision.db')

def get_sqlite_conn():
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create all SQLite tables and seed default users if not present."""
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    with get_sqlite_conn() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            date_of_birth TEXT,
            gender TEXT,
            blood_group TEXT,
            address TEXT,
            height TEXT,
            weight TEXT,
            allergies TEXT,
            conditions TEXT,
            emergency_contact TEXT,
            face_embedding TEXT,
            face_registered INTEGER DEFAULT 0,
            profile_photo TEXT,
            health_score INTEGER DEFAULT 75,
            role TEXT DEFAULT 'patient',
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_records (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            phone TEXT,
            otp_code TEXT NOT NULL,
            purpose TEXT DEFAULT 'login',
            is_used INTEGER DEFAULT 0,
            expires_at TEXT,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_activity (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            login_method TEXT,
            face_confidence REAL,
            success INTEGER DEFAULT 1,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            doctor_id TEXT,
            doctor_name TEXT,
            specialty TEXT,
            appointment_date TEXT,
            appointment_time TEXT,
            duration_minutes INTEGER DEFAULT 30,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            meeting_link TEXT,
            notes TEXT,
            payment_status TEXT DEFAULT 'unpaid',
            payment_amount REAL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            appointment_id TEXT,
            user_id TEXT,
            amount REAL,
            currency TEXT DEFAULT 'INR',
            payment_method TEXT,
            transaction_id TEXT,
            status TEXT DEFAULT 'pending',
            gateway_response TEXT,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            doctor_id TEXT,
            appointment_id TEXT,
            doctor_name TEXT,
            diagnosis TEXT,
            medicines TEXT,
            notes TEXT,
            follow_up_date TEXT,
            pdf_url TEXT,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS disease_predictions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            symptoms TEXT,
            predictions TEXT,
            top_disease TEXT,
            confidence REAL,
            health_risk_score INTEGER,
            recommendations TEXT,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vitals (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            heart_rate INTEGER,
            blood_pressure_sys INTEGER,
            blood_pressure_dia INTEGER,
            temperature REAL,
            oxygen_saturation INTEGER,
            weight REAL,
            height REAL,
            bmi REAL,
            recorded_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            message TEXT,
            type TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS vision_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            session_start TEXT,
            session_end TEXT,
            fatigue_alerts INTEGER DEFAULT 0,
            posture_alerts INTEGER DEFAULT 0,
            blink_count INTEGER DEFAULT 0,
            avg_heart_rate INTEGER,
            skin_analysis TEXT,
            mask_detected INTEGER DEFAULT 0,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            role TEXT,
            message TEXT,
            created_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_records (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            record_type TEXT,
            title TEXT,
            data TEXT,
            file_url TEXT,
            recorded_at TEXT,
            created_at TEXT
        )
        ''')

        conn.commit()

        # Seed initial accounts if table empty
        cursor.execute('SELECT COUNT(*) as count FROM users')
        if cursor.fetchone()['count'] == 0:
            now = datetime.utcnow().isoformat()
            demo_pw = bcrypt.hashpw('demo123'.encode(), bcrypt.gensalt()).decode()
            doc_pw = bcrypt.hashpw('doctor123'.encode(), bcrypt.gensalt()).decode()
            
            seeds = [
                (str(uuid.uuid4()), 'Demo Patient', 'demo@medivision.ai', '+919876543200', demo_pw, '1995-05-15', 'Other', 'O+', 'patient', 82, now, now),
                (str(uuid.uuid4()), 'Dr. Priya Sharma', 'dr.priya@medivision.ai', '+919876543210', doc_pw, '1985-02-20', 'Female', 'A+', 'doctor', 95, now, now),
                (str(uuid.uuid4()), 'Dr. Rahul Mehta', 'dr.rahul@medivision.ai', '+919876543211', doc_pw, '1982-11-10', 'Male', 'B+', 'doctor', 95, now, now),
                (str(uuid.uuid4()), 'Dr. Ananya Patel', 'dr.ananya@medivision.ai', '+919876543212', doc_pw, '1990-07-04', 'Female', 'O+', 'doctor', 95, now, now),
                (str(uuid.uuid4()), 'Dr. Vikram Singh', 'dr.vikram@medivision.ai', '+919876543213', doc_pw, '1978-09-18', 'Male', 'AB+', 'doctor', 95, now, now),
            ]
            cursor.executemany('''
            INSERT INTO users (id, full_name, email, phone, password_hash, date_of_birth, gender, blood_group, role, health_score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', seeds)
            conn.commit()

init_db()

# ============================================================
# SQLite Query Builder (Supabase-compatible interface)
# ============================================================

class QueryResult:
    def __init__(self, data):
        self.data = data

class SQLiteTableQuery:
    def __init__(self, table_name):
        self.table_name = table_name
        self.select_cols = '*'
        self.where_clauses = []
        self.params = []
        self.order_by = None
        self.limit_val = None
        self._action = 'select'
        self._insert_data = None
        self._update_data = None

    def select(self, cols='*'):
        self.select_cols = cols
        self._action = 'select'
        return self

    def eq(self, column, value):
        if value is True:
            self.where_clauses.append(f"({column} = 1 OR {column} = 'true' OR {column} = 'TRUE')")
        elif value is False:
            self.where_clauses.append(f"({column} = 0 OR {column} = 'false' OR {column} = 'FALSE' OR {column} IS NULL)")
        else:
            self.where_clauses.append(f"{column} = ?")
            self.params.append(value)
        return self

    def ilike(self, column, pattern):
        self.where_clauses.append(f"{column} LIKE ?")
        self.params.append(pattern)
        return self

    def order(self, column, desc=False):
        self.order_by = f"{column} {'DESC' if desc else 'ASC'}"
        return self

    def limit(self, count):
        self.limit_val = count
        return self

    def insert(self, record_or_list):
        self._action = 'insert'
        self._insert_data = record_or_list if isinstance(record_or_list, list) else [record_or_list]
        return self

    def update(self, record):
        self._action = 'update'
        self._update_data = record
        return self

    def delete(self):
        self._action = 'delete'
        return self

    def execute(self):
        init_db()
        with get_sqlite_conn() as conn:
            cursor = conn.cursor()

            if self._action == 'insert':
                inserted_rows = []
                for item in self._insert_data:
                    row_dict = dict(item)
                    if 'id' not in row_dict or not row_dict['id']:
                        row_dict['id'] = str(uuid.uuid4())
                    if 'created_at' not in row_dict:
                        row_dict['created_at'] = datetime.utcnow().isoformat()
                    
                    # Serialize dicts/lists to JSON
                    for k, v in row_dict.items():
                        if isinstance(v, (dict, list)):
                            row_dict[k] = json.dumps(v)
                        elif isinstance(v, bool):
                            row_dict[k] = 1 if v else 0

                    cols = list(row_dict.keys())
                    placeholders = ', '.join(['?'] * len(cols))
                    sql = f"INSERT INTO {self.table_name} ({', '.join(cols)}) VALUES ({placeholders})"
                    cursor.execute(sql, list(row_dict.values()))
                    inserted_rows.append(row_dict)
                conn.commit()
                return QueryResult(inserted_rows)

            elif self._action == 'update':
                set_clauses = []
                set_params = []
                for k, v in self._update_data.items():
                    set_clauses.append(f"{k} = ?")
                    if isinstance(v, (dict, list)):
                        set_params.append(json.dumps(v))
                    elif isinstance(v, bool):
                        set_params.append(1 if v else 0)
                    else:
                        set_params.append(v)
                
                where_sql = f" WHERE {' AND '.join(self.where_clauses)}" if self.where_clauses else ""
                sql = f"UPDATE {self.table_name} SET {', '.join(set_clauses)}{where_sql}"
                cursor.execute(sql, set_params + self.params)
                conn.commit()

                # Return updated rows if matched
                if where_sql:
                    cursor.execute(f"SELECT * FROM {self.table_name}{where_sql}", self.params)
                    rows = [self._format_row(dict(r)) for r in cursor.fetchall()]
                    return QueryResult(rows)
                return QueryResult([self._update_data])

            elif self._action == 'delete':
                where_sql = f" WHERE {' AND '.join(self.where_clauses)}" if self.where_clauses else ""
                sql = f"DELETE FROM {self.table_name}{where_sql}"
                cursor.execute(sql, self.params)
                conn.commit()
                return QueryResult([])

            else:  # select
                where_sql = f" WHERE {' AND '.join(self.where_clauses)}" if self.where_clauses else ""
                order_sql = f" ORDER BY {self.order_by}" if self.order_by else ""
                limit_sql = f" LIMIT {self.limit_val}" if self.limit_val else ""
                
                cols = self.select_cols if self.select_cols != '*' else '*'
                sql = f"SELECT {cols} FROM {self.table_name}{where_sql}{order_sql}{limit_sql}"
                cursor.execute(sql, self.params)
                rows = [self._format_row(dict(r)) for r in cursor.fetchall()]
                return QueryResult(rows)

    def _format_row(self, r):
        # Decode JSON fields automatically
        json_fields = ['medicines', 'symptoms', 'predictions', 'recommendations', 'data', 'skin_analysis', 'gateway_response']
        for f in json_fields:
            if f in r and isinstance(r[f], str):
                try:
                    r[f] = json.loads(r[f])
                except:
                    pass
        # Convert integer booleans
        bool_fields = ['is_used', 'face_registered', 'is_active', 'is_read', 'mask_detected', 'success']
        for bf in bool_fields:
            if bf in r and r[bf] is not None:
                r[bf] = bool(r[bf])
        return r

class SQLiteClient:
    def table(self, table_name):
        return SQLiteTableQuery(table_name)

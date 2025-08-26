import sqlite3
import pickle

def get_connection():
    return sqlite3.connect("attendance.db")

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            rollno TEXT PRIMARY KEY,
            name TEXT,
            face_encoding BLOB
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            rollno TEXT,
            date TEXT,
            punch_in TEXT,
            punch_out TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_student(rollno, name, encoding):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO students VALUES (?, ?, ?)",
              (rollno, name, pickle.dumps(encoding)))
    conn.commit()
    conn.close()

def get_students():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    data = c.fetchall()
    conn.close()
    return [(r, n, pickle.loads(enc)) for r, n, enc in data]

def mark_attendance(rollno, today, now):
    conn = get_connection()
    c = conn.cursor()

    # Check if student already has entry for today
    c.execute("SELECT punch_in, punch_out FROM attendance WHERE rollno=? AND date=?", (rollno, today))
    record = c.fetchone()

    if record is None:
        # First time → Punch In
        c.execute("INSERT INTO attendance VALUES (?, ?, ?, ?)", (rollno, today, now, None))
        conn.commit()
        conn.close()
        return "in"   # marked as Punch In

    elif record[0] is not None and record[1] is None:
        # Already punched in, now Punch Out
        c.execute("UPDATE attendance SET punch_out=? WHERE rollno=? AND date=?", (now, rollno, today))
        conn.commit()
        conn.close()
        return "out"  # marked as Punch Out

    else:
        conn.close()
        return "done" # Already punched in & out


def get_attendance():
    conn = get_connection()
    df = None
    try:
        import pandas as pd
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
    except Exception:
        pass
    conn.close()
    return df

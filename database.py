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

import numpy as np

def add_student(rollno, name, encoding):
    conn = get_connection()
    c = conn.cursor()

    # Check if rollno or name already exists
    c.execute("SELECT rollno, name, face_encoding FROM students")
    all_students = c.fetchall()

    for r, n, enc in all_students:
        # Check duplicate roll number or name
        if r == rollno:
            conn.close()
            return "duplicate_roll"
        if n.lower() == name.lower():
            conn.close()
            return "duplicate_name"

        # Check duplicate face using numpy
        stored_encoding = pickle.loads(enc)
        distance = np.linalg.norm(stored_encoding - encoding)
        if distance < 0.45:   # Threshold (tune if needed)
            conn.close()
            return "duplicate_face"

    # If no duplicates, insert new student
    c.execute("INSERT INTO students VALUES (?, ?, ?)", (rollno, name, pickle.dumps(encoding)))
    conn.commit()
    conn.close()
    return "success"


def get_students():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    data = c.fetchall()
    conn.close()
    return [(r, n, pickle.loads(enc)) for r, n, enc in data]

from datetime import datetime

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
        return "in"   # Punch In recorded

    elif record[0] is not None and record[1] is None:
        # Already punched in, now trying Punch Out
        punch_in_time = datetime.strptime(record[0], "%H:%M:%S")
        punch_out_time = datetime.strptime(now, "%H:%M:%S")

        worked_hours = (punch_out_time - punch_in_time).total_seconds() / 3600.0

        if worked_hours < 4:   # Minimum 4 hours required
            conn.close()
            return "too_early"  # Punch out denied
        else:
            c.execute("UPDATE attendance SET punch_out=? WHERE rollno=? AND date=?", (now, rollno, today))
            conn.commit()
            conn.close()
            return "out"  # Punch Out recorded

    else:
        conn.close()
        return "done" # Already punched in & out



def get_attendance():
    conn = get_connection()
    df = None
    try:
        import pandas as pd
        df = pd.read_sql_query("""
            SELECT a.rollno, s.name, a.date, a.punch_in, a.punch_out
            FROM attendance a
            JOIN students s ON a.rollno = s.rollno
            ORDER BY a.date DESC, a.punch_in ASC
        """, conn)
    except Exception:
        pass
    conn.close()
    return df

def get_defaulters():
    conn = get_connection()
    import pandas as pd

    # Get all students
    students = pd.read_sql_query("SELECT rollno, name FROM students", conn)

    # Get all attendance records
    attendance = pd.read_sql_query("SELECT rollno, date FROM attendance", conn)

    conn.close()

    if attendance.empty:
        return pd.DataFrame(columns=["Roll No", "Name", "Status"])

    # Convert date to datetime
    attendance["date"] = pd.to_datetime(attendance["date"])

    # Prepare result
    defaulters_list = []

    for _, student in students.iterrows():
        rollno, name = student["rollno"], student["name"]

        # Filter student's attendance
        stu_att = attendance[attendance["rollno"] == rollno].sort_values("date")

        if stu_att.empty:
            # Never attended → already defaulter
            defaulters_list.append({"Roll No": rollno, "Name": name, "Status": "Defaulter"})
            continue

        # Get unique dates attended
        attended_dates = set(stu_att["date"].dt.date)

        # Create full date range from first to last date
        full_range = pd.date_range(stu_att["date"].min(), stu_att["date"].max())

        # Check consecutive absences
        consecutive_absent = 0
        is_defaulter = False
        for day in full_range:
            if day.date() not in attended_dates:
                consecutive_absent += 1
                if consecutive_absent >= 2:  # Rule: 2 consecutive days
                    is_defaulter = True
                    break
            else:
                consecutive_absent = 0

        defaulters_list.append({
            "Roll No": rollno,
            "Name": name,
            "Status": "Not Regular" if is_defaulter else "Regular"
        })

    return pd.DataFrame(defaulters_list)


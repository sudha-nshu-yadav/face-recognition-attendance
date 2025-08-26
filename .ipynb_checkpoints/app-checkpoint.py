import streamlit as st
import datetime
import pandas as pd
from database import init_db, add_student, get_students, mark_attendance, get_attendance
from face_utils import capture_face, recognize_face

st.set_page_config(page_title="Face Attendance System", layout="wide")
init_db()

st.title("🎓 Face Recognition Attendance System")

menu = ["Register Student", "Mark Attendance", "Attendance Records", "Reports"]
choice = st.sidebar.radio("Menu", menu)

if choice == "Register Student":
    st.header("📝 Register New Student")
    name = st.text_input("Enter Name")
    rollno = st.text_input("Enter Roll No")
    if st.button("Capture & Save Face"):
        encoding = capture_face()
        if encoding is not None:
            add_student(rollno, name, encoding)
            st.success(f"Student {name} ({rollno}) registered successfully!")
        else:
            st.error("No face detected, try again.")

elif choice == "Mark Attendance":
    st.header("📸 Mark Attendance")
    students = get_students()
    if st.button("Recognize & Mark"):
        result = recognize_face(students)
        if result:
            rollno, name = result
            now = str(datetime.datetime.now().time())[:8]
            today = str(datetime.date.today())
            status = mark_attendance(rollno, today, now)

            if status == "in":
                st.success(f"✅ Punch In recorded for {name} ({rollno}) at {now}")
            elif status == "out":
                st.success(f"✅ Punch Out recorded for {name} ({rollno}) at {now}")
            else:
                st.warning(f"⚠️ {name} ({rollno}) already marked for today.")
        else:
            st.error("Face not recognized!")


elif choice == "Attendance Records":
    st.header("📋 Attendance Records")
    df = get_attendance()
    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.info("No attendance records yet.")

elif choice == "Reports":
    st.header("📊 Reports & Analysis")
    df = get_attendance()
    if df is not None and not df.empty:
        monthly = df.groupby("rollno")["date"].count()
        st.bar_chart(monthly)

        avg = monthly.mean()
        st.write(f"📌 Average Attendance: {avg:.2f}")

        threshold = 20
        regular = monthly[monthly >= threshold]
        defaulters = monthly[monthly < threshold]

        st.subheader("✅ Regular Students")
        st.write(regular)

        st.subheader("⚠️ Defaulters")
        st.write(defaulters)
    else:
        st.info("No data available yet.")

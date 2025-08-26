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

    if st.button("Capture & Register", key="register_btn"):

        if not name or not rollno:
            st.error("⚠️ Please enter both Name and Roll.No before capturing.")
        else:
            encoding = capture_face()
            if encoding is not None:
                result = add_student(rollno, name, encoding)
                if result == "success":
                    st.success(f"✅ Student {name} ({rollno}) registered successfully!")
                elif result == "duplicate_roll":
                    st.warning(f"⚠️ Roll No {rollno} already exists!")
                elif result == "duplicate_name":
                    st.warning(f"⚠️ Name {name} already exists!")
                elif result == "duplicate_face":
                    st.warning("⚠️ This face already exists in the database!")
            else:
                st.error("❌ No face detected, please try again.")



elif choice == "Mark Attendance":
    st.header("📸 Mark Attendance")
    students = get_students()
    if st.button("Mark Attendance", key="attendance_btn"):
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
            elif status == "too_early":
                st.warning(f"⚠️ Punch Out denied for {name} ({rollno}). Minimum 4 hours required!")
            else:
                st.info(f"ℹ️ {name} ({rollno}) already marked for today.")
        else:
            st.error("❌ Face not recognized!")



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

        from database import get_defaulters
        defaulters_df = get_defaulters()

        st.subheader("Student List")
        st.dataframe(defaulters_df)
    else:
        st.info("No data available yet.")


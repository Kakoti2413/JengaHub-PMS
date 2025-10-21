import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.express as px
import os

# ===================== CUSTOM CSS FOR YELLOW MAIN CONTENT =====================
st.markdown("""
<style>
    /* Yellow background for main content */
    .stApp {
        background-color: #FFD700;
    }
    
    .main .block-container {
        background-color: transparent;
        padding: 20px;
    }
    
    /* Ensure text is readable on yellow background */
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: #000000 !important;
    }
    
    .main p, .main div, .main span {
        color: #000000 !important;
    }
    
    /* Dataframes should have white background for readability */
    .main .dataframe {
        background-color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ===================== DATABASE SETUP =====================
conn = sqlite3.connect('school_management.db', check_same_thread=False)
cursor = conn.cursor()

# Schools Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS schools (
    school_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)
''')

# Students Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER,
    name TEXT,
    age INTEGER,
    grade TEXT,
    parent_name TEXT,
    parent_contact TEXT,
    FOREIGN KEY(school_id) REFERENCES schools(school_id)
)
''')

# Attendance & Behaviour Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    school_id INTEGER,
    date TEXT,
    status TEXT,
    behaviour_score INTEGER,
    behaviour_comment TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(school_id) REFERENCES schools(school_id)
)
''')

# Assessments Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    school_id INTEGER,
    date TEXT,
    subject TEXT,
    marks INTEGER,
    total INTEGER,
    grade TEXT,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(school_id) REFERENCES schools(school_id)
)
''')

# Teachers Table (NEW)
cursor.execute('''
CREATE TABLE IF NOT EXISTS teachers (
    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER,
    name TEXT,
    email TEXT,
    phone TEXT,
    subject TEXT,
    qualification TEXT,
    join_date TEXT,
    status TEXT DEFAULT 'Active',
    FOREIGN KEY(school_id) REFERENCES schools(school_id)
)
''')

# Teacher Assignments Table (NEW)
cursor.execute('''
CREATE TABLE IF NOT EXISTS teacher_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER,
    school_id INTEGER,
    class_grade TEXT,
    subject TEXT,
    academic_year TEXT,
    FOREIGN KEY(teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY(school_id) REFERENCES schools(school_id)
)
''')
conn.commit()

# ===================== SIDEBAR =====================
try:
    st.sidebar.image("logo.png")
    st.sidebar.title("Jenga Hub PMS")
except:
    st.sidebar.markdown("---")

st.sidebar.title("Navigation")
menu = st.sidebar.radio("Navigation", [
    "Schools", 
    "Teachers", 
    "Students", 
    "Attendance & Behaviour", 
    "Assessments", 
    "Analytics", 
    "Reports",
    "Teacher Portal",
    "Parent Portal",
    "Export Data", 
    "System Admin"
])

# ===================== SCHOOLS =====================
if menu == "Schools":
    st.header("🏫 Manage Schools")
    school_name = st.text_input("Add a New School")
    if st.button("Add School") and school_name:
        try:
            cursor.execute("INSERT INTO schools (name) VALUES (?)", (school_name,))
            conn.commit()
            st.success(f"School '{school_name}' added successfully!")
            st.rerun()
        except:
            st.error("School already exists!")

    st.subheader("Existing Schools")
    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    st.dataframe(df_schools)

# ===================== TEACHERS (NEW) =====================
elif menu == "Teachers":
    st.header("👨‍🏫 Teacher Management")
    
    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    if df_schools.empty:
        st.warning("No schools available. Please add a school first!")
    else:
        school_select = st.selectbox("Select School", df_schools['name'])
        school_id = df_schools[df_schools['name'] == school_select]['school_id'].values[0]
        
        # Add Teacher Form
        with st.form("add_teacher_form", clear_on_submit=True):
            st.subheader("➕ Add New Teacher")
            col1, col2 = st.columns(2)
            with col1:
                t_name = st.text_input("Teacher Name")
                t_email = st.text_input("Email")
                t_phone = st.text_input("Phone Number")
            with col2:
                t_subject = st.text_input("Subject Specialization")
                t_qualification = st.text_input("Qualification")
                t_join_date = st.date_input("Join Date")
            
            submitted = st.form_submit_button("Add Teacher")
            if submitted:
                if t_name.strip():
                    cursor.execute('''
                        INSERT INTO teachers (school_id, name, email, phone, subject, qualification, join_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (school_id, t_name, t_email, t_phone, t_subject, t_qualification, str(t_join_date)))
                    conn.commit()
                    st.success(f"Teacher '{t_name}' added successfully!")
                    st.rerun()
        
        # Teacher List
        df_teachers = pd.read_sql_query("SELECT * FROM teachers WHERE school_id=?", conn, params=(school_id,))
        st.subheader("📋 Teaching Staff")
        if not df_teachers.empty:
            st.dataframe(df_teachers)
            
            # Teacher Assignments
            st.subheader("📚 Class Assignments")
            selected_teacher = st.selectbox("Select Teacher", df_teachers['name'].tolist())
            teacher_id = df_teachers[df_teachers['name'] == selected_teacher]['teacher_id'].values[0]
            
            with st.form("assignment_form"):
                col1, col2 = st.columns(2)
                with col1:
                    assign_class = st.text_input("Class/Grade")
                    assign_subject = st.text_input("Subject")
                with col2:
                    academic_year = st.text_input("Academic Year", "2024-2025")
                
                if st.form_submit_button("Assign Class"):
                    cursor.execute('''
                        INSERT INTO teacher_assignments (teacher_id, school_id, class_grade, subject, academic_year)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (teacher_id, school_id, assign_class, assign_subject, academic_year))
                    conn.commit()
                    st.success("Class assigned successfully!")
                    st.rerun()
        else:
            st.info("No teachers found for this school.")

# ===================== STUDENTS =====================
elif menu == "Students":
    st.header("🧑‍🎓 Manage Students")

    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    if df_schools.empty:
        st.warning("No schools available. Please add a school first!")
    else:
        school_select = st.selectbox("Select School", df_schools['name'])
        school_id = df_schools[df_schools['name'] == school_select]['school_id'].values[0]

        with st.form("add_student_form", clear_on_submit=True):
            st.subheader("➕ Add New Student")
            s_name = st.text_input("Student Name")
            s_age = st.number_input("Age", min_value=1, max_value=30, step=1)
            s_grade = st.text_input("Grade/Class")
            s_parent = st.text_input("Parent/Guardian Name")
            s_contact = st.text_input("Parent Contact Number")
            submitted = st.form_submit_button("Add Student")

            if submitted:
                if s_name.strip():
                    try:
                        cursor.execute('''
                            INSERT INTO students (school_id, name, age, grade, parent_name, parent_contact)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (school_id, s_name.strip(), s_age, s_grade, s_parent, s_contact))
                        conn.commit()
                        st.success(f"Student '{s_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding student: {e}")
                else:
                    st.error("Student name is required!")

        df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
        st.subheader("📋 Existing Students")
        
        if df_students.empty:
            st.info("No students found for this school.")
        else:
            st.dataframe(df_students)

        if not df_students.empty:
            selected_id = st.selectbox("Select Student ID to Edit/Delete", df_students['student_id'].tolist())
            student = df_students[df_students['student_id'] == selected_id].iloc[0]

            s_edit_name = st.text_input("Student Name", student['name'])
            s_edit_age = st.number_input("Age", min_value=1, max_value=30, value=student['age'], step=1)
            s_edit_grade = st.text_input("Grade/Class", student['grade'])
            s_edit_parent = st.text_input("Parent Name", student['parent_name'])
            s_edit_contact = st.text_input("Parent Contact", student['parent_contact'])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Student"):
                    if s_edit_name.strip():
                        cursor.execute('''
                            UPDATE students 
                            SET name=?, age=?, grade=?, parent_name=?, parent_contact=?
                            WHERE student_id=?
                        ''', (s_edit_name, s_edit_age, s_edit_grade, s_edit_parent, s_edit_contact, selected_id))
                        conn.commit()
                        st.success("Student updated successfully!")
                        st.rerun()
                    else:
                        st.error("Student name is required!")
            
            with col2:
                if st.button("Delete Student"):
                    cursor.execute("DELETE FROM students WHERE student_id=?", (selected_id,))
                    conn.commit()
                    st.success("Student deleted successfully!")
                    st.rerun()

# ===================== ATTENDANCE & BEHAVIOUR =====================
elif menu == "Attendance & Behaviour":
    st.header("✅ Record Attendance & Behaviour")
    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    
    if df_schools.empty:
        st.warning("No schools available. Please add a school first!")
    else:
        school_select = st.selectbox("Select School", df_schools['name'])
        
        if school_select:
            school_id = df_schools[df_schools['name']==school_select]['school_id'].values[0]
            
            df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
            
            if df_students.empty:
                st.warning("No students found for this school. Please add students first.")
            else:
                st.subheader(f"📋 Students in {school_select}")
                st.dataframe(df_students[['student_id', 'name', 'grade', 'age']])
                
                st.subheader("🎯 Record Attendance & Behaviour")
                date = st.date_input("Select Date")
                
                if date:
                    with st.form("attendance_form"):
                        attendance_data = []
                        
                        st.write("### Set attendance and behaviour for each student:")
                        
                        for idx, row in df_students.iterrows():
                            st.markdown(f"---")
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.write(f"**{row['name']}**")
                                st.write(f"Grade: {row['grade']}, Age: {row['age']}")
                            with col2:
                                col2a, col2b, col2c = st.columns(3)
                                with col2a:
                                    status = st.selectbox(
                                        "Attendance", 
                                        ["Present", "Absent", "Late"], 
                                        key=f"status_{row['student_id']}"
                                    )
                                with col2b:
                                    behaviour_score = st.slider(
                                        "Behaviour", 
                                        1, 5, 3, 
                                        key=f"behaviour_{row['student_id']}"
                                    )
                                with col2c:
                                    behaviour_comment = st.text_input(
                                        "Comments", 
                                        key=f"comment_{row['student_id']}"
                                    )
                            
                            attendance_data.append({
                                'student_id': row['student_id'],
                                'name': row['name'],
                                'status': status,
                                'behaviour_score': behaviour_score,
                                'behaviour_comment': behaviour_comment
                            })
                        
                        submitted = st.form_submit_button("💾 Save All Attendance Records")
                        
                        if submitted:
                            success_count = 0
                            for data in attendance_data:
                                try:
                                    cursor.execute('''
                                        INSERT INTO attendance (student_id, school_id, date, status, behaviour_score, behaviour_comment)
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    ''', (data['student_id'], school_id, str(date), data['status'], data['behaviour_score'], data['behaviour_comment']))
                                    success_count += 1
                                except Exception as e:
                                    st.error(f"Error saving record for {data['name']}: {e}")
                            
                            conn.commit()
                            st.success(f"✅ Successfully saved attendance records for {success_count} out of {len(attendance_data)} students!")
                            st.rerun()

# ===================== ASSESSMENTS =====================
elif menu == "Assessments":
    st.header("📝 Record Assessments")
    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    
    if df_schools.empty:
        st.warning("No schools available. Please add a school first!")
    else:
        school_select = st.selectbox("Select School", df_schools['name'])
        
        if school_select:
            school_id = df_schools[df_schools['name']==school_select]['school_id'].values[0]
            
            df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
            
            if df_students.empty:
                st.warning("No students found for this school. Please add students first.")
            else:
                st.subheader(f"📋 Students in {school_select}")
                st.dataframe(df_students[['student_id', 'name', 'grade', 'age']])
                
                st.subheader("🎯 Record Assessments")
                
                col1, col2 = st.columns(2)
                with col1:
                    date = st.date_input("Assessment Date")
                    subject = st.text_input("Subject")
                with col2:
                    total_marks = st.number_input("Total Marks", min_value=1, value=100, step=1)
                
                if date and subject and total_marks:
                    with st.form("assessment_form"):
                        assessment_data = []
                        
                        st.write("### Enter marks for each student:")
                        
                        for idx, row in df_students.iterrows():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.write(f"**{row['name']}**")
                                st.write(f"Grade: {row['grade']}")
                            with col2:
                                marks = st.number_input(
                                    "Marks", 
                                    min_value=0, 
                                    max_value=total_marks, 
                                    value=0,
                                    key=f"marks_{row['student_id']}"
                                )
                            with col3:
                                percentage = (marks / total_marks) * 100 if total_marks > 0 else 0
                                if percentage >= 90:
                                    grade = "A"
                                elif percentage >= 80:
                                    grade = "B"
                                elif percentage >= 70:
                                    grade = "C"
                                elif percentage >= 60:
                                    grade = "D"
                                else:
                                    grade = "E"
                                
                                st.write(f"**Grade: {grade}**")
                                st.write(f"({percentage:.1f}%)")
                            
                            assessment_data.append({
                                'student_id': row['student_id'],
                                'name': row['name'],
                                'marks': marks,
                                'total': total_marks,
                                'grade': grade
                            })
                        
                        submitted = st.form_submit_button("💾 Save All Assessment Records")
                        
                        if submitted:
                            success_count = 0
                            for data in assessment_data:
                                try:
                                    cursor.execute('''
                                        INSERT INTO assessments (student_id, school_id, date, subject, marks, total, grade)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                    ''', (data['student_id'], school_id, str(date), subject, data['marks'], data['total'], data['grade']))
                                    success_count += 1
                                except Exception as e:
                                    st.error(f"Error saving assessment for {data['name']}: {e}")
                            
                            conn.commit()
                            st.success(f"✅ Successfully saved assessment records for {success_count} out of {len(assessment_data)} students!")
                            st.rerun()

## ===================== ANALYTICS (ENHANCED) - FIXED VERSION =====================
elif menu == "Analytics":
    st.header("📊 Advanced Analytics & M&E Dashboard")
    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    
    if df_schools.empty:
        st.warning("No schools available. Please add a school first!")
    else:
        school_select = st.selectbox("Select School", df_schools['name'])
        school_id = df_schools[df_schools['name']==school_select]['school_id'].values[0]
        
        # Time period selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now().replace(month=1, day=1))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Alert System
        def check_alerts(school_id, start_date, end_date):
            alerts = []
            df_attendance = pd.read_sql_query(
                "SELECT * FROM attendance WHERE school_id=? AND date BETWEEN ? AND ?", 
                conn, params=(school_id, str(start_date), str(end_date))
            )
            
            if not df_attendance.empty:
                # Low attendance alert
                attendance_rate = (df_attendance['status'] == 'Present').mean() * 100
                if attendance_rate < 80:
                    alerts.append(f"⚠️ Low attendance rate: {attendance_rate:.1f}%")
                
                # Poor behaviour alert
                avg_behaviour = df_attendance['behaviour_score'].mean()
                if avg_behaviour < 2.5:
                    alerts.append(f"😟 Low average behaviour score: {avg_behaviour:.1f}/5")
            
            return alerts
        
        alerts = check_alerts(school_id, start_date, end_date)
        if alerts:
            st.subheader("🚨 System Alerts")
            for alert in alerts:
                st.warning(alert)
        
        # Key Performance Indicators
        st.subheader("📈 Key Performance Indicators")
        
        df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
        df_attendance = pd.read_sql_query(
            "SELECT * FROM attendance WHERE school_id=? AND date BETWEEN ? AND ?", 
            conn, params=(school_id, str(start_date), str(end_date))
        )
        df_assessments = pd.read_sql_query(
            "SELECT * FROM assessments WHERE school_id=? AND date BETWEEN ? AND ?", 
            conn, params=(school_id, str(start_date), str(end_date))
        )
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_students = len(df_students)
            st.metric("Total Students", total_students)
        
        with col2:
            attendance_rate = (len(df_attendance[df_attendance['status'] == 'Present']) / len(df_attendance) * 100) if len(df_attendance) > 0 else 0
            st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
        
        with col3:
            avg_behaviour = df_attendance['behaviour_score'].mean() if not df_attendance.empty else 0
            st.metric("Avg Behaviour", f"{avg_behaviour:.1f}/5")
        
        with col4:
            avg_marks = df_assessments['marks'].mean() if not df_assessments.empty else 0
            st.metric("Avg Marks", f"{avg_marks:.1f}%")
        
        # Trend Analysis
        st.subheader("📅 Trend Analysis")
        
        if not df_attendance.empty:
            try:
                df_attendance['date'] = pd.to_datetime(df_attendance['date'])
                monthly_attendance = df_attendance.groupby(df_attendance['date'].dt.to_period('M'))['status'].apply(
                    lambda x: (x == 'Present').sum() / len(x) * 100
                ).reset_index()
                monthly_attendance['date'] = monthly_attendance['date'].astype(str)
                
                fig_trend = px.line(monthly_attendance, x='date', y='status', 
                                   title='Monthly Attendance Trend', markers=True)
                st.plotly_chart(fig_trend)
            except Exception as e:
                st.error(f"Error generating trend analysis: {e}")
        
        # Performance by Grade - COMPLETELY FIXED VERSION
        st.subheader("🎯 Performance by Grade")
        if not df_assessments.empty and not df_students.empty:
            try:
                # Debug: Check what columns we have
                st.write("🔍 Debug Info:")
                st.write(f"Assessments columns: {list(df_assessments.columns)}")
                st.write(f"Students columns: {list(df_students.columns)}")
                
                # Merge assessments with student data
                df_merged = df_assessments.merge(df_students[['student_id', 'grade']], on='student_id', how='left')
                
                # Debug: Check merged data
                st.write(f"Merged columns: {list(df_merged.columns)}")
                st.write(f"Sample merged data:")
                st.dataframe(df_merged.head(3))
                
                # SAFE GRADE PERFORMANCE CALCULATION
                if 'grade' in df_merged.columns:
                    # Check if we have any non-null grade values
                    if df_merged['grade'].notna().any():
                        grade_performance = df_merged.groupby('grade')['marks'].agg(['mean', 'count']).round(2)
                        grade_performance.columns = ['Average Marks', 'Number of Assessments']
                        st.dataframe(grade_performance)
                        
                        # Visualize grade performance
                        fig_grade = px.bar(grade_performance.reset_index(), 
                                          x='grade', y='Average Marks',
                                          title='Average Marks by Grade',
                                          color='Average Marks')
                        st.plotly_chart(fig_grade)
                    else:
                        st.info("No grade data available (all grade values are null).")
                        
                        # Show performance by subject instead
                        st.subheader("📚 Performance by Subject")
                        subject_performance = df_assessments.groupby('subject')['marks'].agg(['mean', 'count']).round(2)
                        subject_performance.columns = ['Average Marks', 'Number of Assessments']
                        st.dataframe(subject_performance)
                else:
                    st.warning("Grade column not found in merged data. Showing performance by subject instead.")
                    
                    # Fallback: Show performance by subject
                    st.subheader("📚 Performance by Subject")
                    subject_performance = df_assessments.groupby('subject')['marks'].agg(['mean', 'count']).round(2)
                    subject_performance.columns = ['Average Marks', 'Number of Assessments']
                    st.dataframe(subject_performance)
                    
            except Exception as e:
                st.error(f"Error generating performance analysis: {str(e)}")
                st.info("Showing basic assessment data instead:")
                st.dataframe(df_assessments.head(10))

        # Original Analytics Charts
        if not df_attendance.empty:
            try:
                att_summary = df_attendance.groupby('status').size().reset_index(name='count')
                fig = px.pie(att_summary, names='status', values='count', title='Attendance Breakdown')
                st.plotly_chart(fig)
            except Exception as e:
                st.error(f"Error generating attendance chart: {e}")

        if not df_attendance.empty and not df_students.empty:
            st.subheader("😊 Behaviour Analytics")
            try:
                df_beh = df_attendance.groupby('student_id')['behaviour_score'].mean().reset_index()
                df_beh = df_beh.merge(df_students[['student_id','name']], on='student_id', how='left')
                
                if len(df_beh) > 15:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("🏆 Top 10 Behaviour Scores")
                        top_students = df_beh.nlargest(10, 'behaviour_score')
                        fig2a = px.bar(top_students, x='name', y='behaviour_score')
                        st.plotly_chart(fig2a, use_container_width=True)
                    
                    with col2:
                        st.write("📈 Behaviour Summary")
                        avg_behaviour = df_beh['behaviour_score'].mean()
                        st.metric("Class Average", f"{avg_behaviour:.1f}/5")
                        st.metric("Highest", f"{df_beh['behaviour_score'].max():.1f}/5")
                        st.metric("Lowest", f"{df_beh['behaviour_score'].min():.1f}/5")
                else:
                    fig2 = px.bar(df_beh, x='name', y='behaviour_score', title='Average Behaviour Score')
                    st.plotly_chart(fig2)
            except Exception as e:
                st.error(f"Error generating behaviour analytics: {e}")

        if not df_assessments.empty:
            st.subheader("📝 Assessment Analytics")
            try:
                df_ass_avg = df_assessments.groupby('subject')['marks'].mean().reset_index()
                fig3 = px.bar(df_ass_avg, x='subject', y='marks', title='Average Marks per Subject')
                st.plotly_chart(fig3)
            except Exception as e:
                st.error(f"Error generating assessment analytics: {e}")

# ===================== REPORTS (COMPLETELY FIXED) =====================
elif menu == "Reports":
    st.header("📑 Comprehensive Reports")
    
    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    if not df_schools.empty:
        school_select = st.selectbox("Select School", df_schools['name'])
        school_id = df_schools[df_schools['name'] == school_select]['school_id'].values[0]
        
        report_type = st.selectbox("Select Report Type", [
            "Student Performance Report",
            "Teacher Performance Report", 
            "Attendance Summary Report",
            "Behaviour Analysis Report",
            "Comprehensive School Report"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Report Start Date")
        with col2:
            report_end = st.date_input("Report End Date")
        
        if st.button("Generate Report"):
            
            # STUDENT PERFORMANCE REPORT - FIXED
            if report_type == "Student Performance Report":
                df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
                df_assessments = pd.read_sql_query(
                    "SELECT * FROM assessments WHERE school_id=? AND date BETWEEN ? AND ?",
                    conn, params=(school_id, str(report_start), str(report_end))
                )
                
                if not df_assessments.empty and not df_students.empty:
                    try:
                        # Safe merge with error handling
                        performance_report = df_assessments.merge(
                            df_students[['student_id', 'name', 'grade']], 
                            on='student_id', 
                            how='left'
                        )
                        
                        st.subheader("📊 Student Performance Report")
                        st.dataframe(performance_report)
                        
                        # SAFE GRADE SUMMARY - No KeyError
                        if 'grade' in performance_report.columns and performance_report['grade'].notna().any():
                            summary = performance_report.groupby('grade').agg({
                                'marks': ['mean', 'max', 'min', 'count'],
                                'student_id': 'nunique'
                            }).round(2)
                            summary.columns = ['Average Marks', 'Highest Marks', 'Lowest Marks', 'Total Assessments', 'Unique Students']
                            st.subheader("🎯 Performance Summary by Grade")
                            st.dataframe(summary)
                            
                            # Visualize grade performance
                            fig_grade = px.bar(summary.reset_index(), 
                                              x='grade', y='Average Marks',
                                              title='Average Marks by Grade',
                                              color='Average Marks')
                            st.plotly_chart(fig_grade)
                        else:
                            st.info("No grade data available for summary.")
                            
                            # Show overall performance instead
                            overall_stats = {
                                'Metric': ['Average Marks', 'Highest Marks', 'Lowest Marks', 'Total Assessments', 'Students Assessed'],
                                'Value': [
                                    f"{performance_report['marks'].mean():.1f}",
                                    f"{performance_report['marks'].max()}",
                                    f"{performance_report['marks'].min()}",
                                    f"{len(performance_report)}",
                                    f"{performance_report['student_id'].nunique()}"
                                ]
                            }
                            st.subheader("📈 Overall Performance Summary")
                            st.dataframe(pd.DataFrame(overall_stats))
                            
                    except Exception as e:
                        st.error(f"Error generating performance report: {e}")
                else:
                    st.info("No assessment data available for the selected period.")
            
            # TEACHER PERFORMANCE REPORT - FIXED
            elif report_type == "Teacher Performance Report":
                df_teachers = pd.read_sql_query("SELECT * FROM teachers WHERE school_id=?", conn, params=(school_id,))
                df_assignments = pd.read_sql_query("SELECT * FROM teacher_assignments WHERE school_id=?", conn, params=(school_id,))
                df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
                df_assessments = pd.read_sql_query(
                    "SELECT * FROM assessments WHERE school_id=? AND date BETWEEN ? AND ?",
                    conn, params=(school_id, str(report_start), str(report_end))
                )
                
                st.subheader("👨‍🏫 Teacher Performance Report")
                
                if not df_teachers.empty:
                    # Teacher basic info
                    st.write("### Teaching Staff")
                    st.dataframe(df_teachers[['name', 'subject', 'qualification', 'join_date', 'status']])
                    
                    # Teacher assignments
                    if not df_assignments.empty:
                        st.write("### Class Assignments")
                        st.dataframe(df_assignments)
                        
                        # Teacher workload summary
                        workload = df_assignments.groupby('teacher_id').agg({
                            'class_grade': 'count',
                            'subject': lambda x: ', '.join(x.unique())
                        }).reset_index()
                        
                        # Merge with teacher names
                        workload = workload.merge(df_teachers[['teacher_id', 'name']], on='teacher_id')
                        workload.columns = ['Teacher ID', 'Number of Classes', 'Subjects', 'Teacher Name']
                        st.write("### Teacher Workload Summary")
                        st.dataframe(workload[['Teacher Name', 'Number of Classes', 'Subjects']])
                    else:
                        st.info("No class assignments found.")
                        
                    # Teacher performance metrics (if assessments exist)
                    if not df_assessments.empty and not df_students.empty:
                        try:
                            # Get classes taught by each teacher
                            teacher_classes = df_assignments.groupby('teacher_id')['class_grade'].unique().reset_index()
                            
                            performance_data = []
                            for _, teacher in df_teachers.iterrows():
                                teacher_id = teacher['teacher_id']
                                teacher_classes_list = teacher_classes[teacher_classes['teacher_id'] == teacher_id]['class_grade'].iloc[0] if not teacher_classes[teacher_classes['teacher_id'] == teacher_id].empty else []
                                
                                if len(teacher_classes_list) > 0:
                                    # Get students in teacher's classes
                                    teacher_students = df_students[df_students['grade'].isin(teacher_classes_list)]
                                    if not teacher_students.empty:
                                        # Get assessments for these students
                                        teacher_assessments = df_assessments[df_assessments['student_id'].isin(teacher_students['student_id'])]
                                        if not teacher_assessments.empty:
                                            avg_marks = teacher_assessments['marks'].mean()
                                            performance_data.append({
                                                'Teacher': teacher['name'],
                                                'Subject': teacher['subject'],
                                                'Classes': ', '.join(teacher_classes_list),
                                                'Average Student Marks': f"{avg_marks:.1f}%",
                                                'Students Assessed': teacher_assessments['student_id'].nunique()
                                            })
                            
                            if performance_data:
                                st.write("### Teacher Performance Metrics")
                                st.dataframe(pd.DataFrame(performance_data))
                                
                        except Exception as e:
                            st.info("Could not calculate teacher performance metrics.")
                else:
                    st.info("No teacher data available.")
            
            # ATTENDANCE SUMMARY REPORT - FIXED
            elif report_type == "Attendance Summary Report":
                df_attendance = pd.read_sql_query(
                    "SELECT * FROM attendance WHERE school_id=? AND date BETWEEN ? AND ?",
                    conn, params=(school_id, str(report_start), str(report_end))
                )
                df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
                
                if not df_attendance.empty:
                    # Basic attendance summary
                    attendance_summary = df_attendance.groupby('status').size().reset_index(name='count')
                    total_records = attendance_summary['count'].sum()
                    attendance_summary['percentage'] = (attendance_summary['count'] / total_records * 100).round(1)
                    
                    st.subheader("✅ Attendance Summary")
                    st.dataframe(attendance_summary)
                    
                    # Attendance trend
                    try:
                        df_attendance['date'] = pd.to_datetime(df_attendance['date'])
                        daily_attendance = df_attendance.groupby('date')['status'].apply(
                            lambda x: (x == 'Present').mean() * 100
                        ).reset_index()
                        daily_attendance.columns = ['Date', 'Attendance Rate']
                        
                        fig_attendance = px.line(daily_attendance, x='Date', y='Attendance Rate', 
                                               title='Daily Attendance Trend', markers=True)
                        st.plotly_chart(fig_attendance)
                    except Exception as e:
                        st.error(f"Error generating attendance trend: {e}")
                    
                    # Attendance by grade (if student data available)
                    if not df_students.empty:
                        try:
                            attendance_with_grades = df_attendance.merge(
                                df_students[['student_id', 'grade']], 
                                on='student_id', 
                                how='left'
                            )
                            
                            if 'grade' in attendance_with_grades.columns and attendance_with_grades['grade'].notna().any():
                                grade_attendance = attendance_with_grades.groupby('grade').agg({
                                    'status': lambda x: (x == 'Present').mean() * 100,
                                    'student_id': 'nunique'
                                }).round(2)
                                grade_attendance.columns = ['Attendance Rate %', 'Number of Students']
                                grade_attendance['Attendance Rate %'] = grade_attendance['Attendance Rate %'].round(1)
                                
                                st.subheader("📊 Attendance by Grade")
                                st.dataframe(grade_attendance)
                        except Exception as e:
                            st.info("Could not generate grade-wise attendance breakdown.")
                            
                else:
                    st.info("No attendance data available for the selected period.")
            
            # BEHAVIOUR ANALYSIS REPORT - FIXED
            elif report_type == "Behaviour Analysis Report":
                df_attendance = pd.read_sql_query(
                    "SELECT * FROM attendance WHERE school_id=? AND date BETWEEN ? AND ?",
                    conn, params=(school_id, str(report_start), str(report_end))
                )
                df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
                
                if not df_attendance.empty:
                    # Behaviour score summary
                    behaviour_stats = {
                        'Metric': ['Average Behaviour Score', 'Highest Score', 'Lowest Score', 'Total Records'],
                        'Value': [
                            f"{df_attendance['behaviour_score'].mean():.1f}/5",
                            f"{df_attendance['behaviour_score'].max()}/5",
                            f"{df_attendance['behaviour_score'].min()}/5",
                            f"{len(df_attendance)}"
                        ]
                    }
                    
                    st.subheader("😊 Behaviour Analysis Summary")
                    st.dataframe(pd.DataFrame(behaviour_stats))
                    
                    # Behaviour score distribution
                    score_distribution = df_attendance['behaviour_score'].value_counts().sort_index().reset_index()
                    score_distribution.columns = ['Behaviour Score', 'Count']
                    
                    fig_behaviour = px.bar(score_distribution, x='Behaviour Score', y='Count',
                                          title='Behaviour Score Distribution')
                    st.plotly_chart(fig_behaviour)
                    
                    # Top and bottom performers
                    if not df_students.empty:
                        try:
                            student_behaviour = df_attendance.groupby('student_id')['behaviour_score'].mean().reset_index()
                            student_behaviour = student_behaviour.merge(
                                df_students[['student_id', 'name', 'grade']], 
                                on='student_id', 
                                how='left'
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("🏆 Top 10 Behaviour Scores")
                                top_performers = student_behaviour.nlargest(10, 'behaviour_score')[['name', 'grade', 'behaviour_score']]
                                st.dataframe(top_performers.round(2))
                            
                            with col2:
                                st.write("📉 Bottom 10 Behaviour Scores")
                                bottom_performers = student_behaviour.nsmallest(10, 'behaviour_score')[['name', 'grade', 'behaviour_score']]
                                st.dataframe(bottom_performers.round(2))
                                
                        except Exception as e:
                            st.info("Could not generate student behaviour rankings.")
                            
                else:
                    st.info("No attendance/behaviour data available for the selected period.")
            
            # COMPREHENSIVE SCHOOL REPORT - FIXED
            elif report_type == "Comprehensive School Report":
                # Gather all data
                df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
                df_teachers = pd.read_sql_query("SELECT * FROM teachers WHERE school_id=?", conn, params=(school_id,))
                df_attendance = pd.read_sql_query(
                    "SELECT * FROM attendance WHERE school_id=? AND date BETWEEN ? AND ?",
                    conn, params=(school_id, str(report_start), str(report_end))
                )
                df_assessments = pd.read_sql_query(
                    "SELECT * FROM assessments WHERE school_id=? AND date BETWEEN ? AND ?",
                    conn, params=(school_id, str(report_start), str(report_end))
                )
                
                st.subheader("🏫 Comprehensive School Report")
                st.write(f"**School:** {school_select}")
                st.write(f"**Report Period:** {report_start} to {report_end}")
                
                # Key Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Students", len(df_students))
                with col2:
                    st.metric("Teaching Staff", len(df_teachers))
                with col3:
                    attendance_rate = (len(df_attendance[df_attendance['status'] == 'Present']) / len(df_attendance) * 100) if len(df_attendance) > 0 else 0
                    st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
                with col4:
                    avg_marks = df_assessments['marks'].mean() if not df_assessments.empty else 0
                    st.metric("Average Marks", f"{avg_marks:.1f}%")
                
                # Detailed Sections
                st.subheader("📋 Student Demographics")
                if not df_students.empty:
                    grade_distribution = df_students['grade'].value_counts().reset_index()
                    grade_distribution.columns = ['Grade', 'Number of Students']
                    st.dataframe(grade_distribution)
                
                st.subheader("📊 Academic Performance")
                if not df_assessments.empty:
                    subject_performance = df_assessments.groupby('subject')['marks'].agg(['mean', 'count']).round(2)
                    subject_performance.columns = ['Average Marks', 'Number of Assessments']
                    st.dataframe(subject_performance)
                
                st.subheader("✅ Attendance Overview")
                if not df_attendance.empty:
                    attendance_breakdown = df_attendance['status'].value_counts().reset_index()
                    attendance_breakdown.columns = ['Status', 'Count']
                    st.dataframe(attendance_breakdown)
                
                st.subheader("👨‍🏫 Teaching Staff Overview")
                if not df_teachers.empty:
                    teacher_summary = df_teachers[['name', 'subject', 'qualification', 'status']]
                    st.dataframe(teacher_summary)
                    
# ===================== TEACHER PORTAL (NEW) =====================
elif menu == "Teacher Portal":
    st.header("👨‍🏫 Teacher Portal")
    
    df_teachers = pd.read_sql_query("SELECT name FROM teachers", conn)
    if not df_teachers.empty:
        teacher_name = st.selectbox("Select Your Name", df_teachers['name'].tolist())
        
        if teacher_name:
            st.success(f"Welcome, {teacher_name}!")
            
            teacher_info = pd.read_sql_query("SELECT * FROM teachers WHERE name=?", conn, params=(teacher_name,))
            teacher_id = teacher_info['teacher_id'].iloc[0]
            school_id = teacher_info['school_id'].iloc[0]
            
            assignments = pd.read_sql_query("SELECT * FROM teacher_assignments WHERE teacher_id=?", conn, params=(teacher_id,))
            
            if not assignments.empty:
                st.subheader("My Classes")
                st.dataframe(assignments)
                
                st.subheader("📝 Quick Attendance")
                selected_class = st.selectbox("Select Class", assignments['class_grade'].unique())
                
                if selected_class:
                    df_students = pd.read_sql_query(
                        "SELECT * FROM students WHERE school_id=? AND grade=?", 
                        conn, params=(school_id, selected_class)
                    )
                    
                    if not df_students.empty:
                        attendance_date = st.date_input("Attendance Date")
                        with st.form("quick_attendance"):
                            for idx, row in df_students.iterrows():
                                status = st.selectbox(
                                    f"{row['name']}",
                                    ["Present", "Absent", "Late"],
                                    key=f"att_{row['student_id']}"
                                )
                            
                            if st.form_submit_button("Save Attendance"):
                                for idx, row in df_students.iterrows():
                                    cursor.execute('''
                                        INSERT INTO attendance (student_id, school_id, date, status, behaviour_score)
                                        VALUES (?, ?, ?, ?, ?)
                                    ''', (row['student_id'], school_id, str(attendance_date), status, 3))
                                conn.commit()
                                st.success("Attendance saved for all students!")
            else:
                st.info("No class assignments found.")
    else:
        st.warning("No teachers available. Please add teachers first.")

# ===================== PARENT PORTAL (NEW) =====================
elif menu == "Parent Portal":
    st.header("👨‍👩‍👧‍👦 Parent Portal")
    
    df_students = pd.read_sql_query("SELECT name FROM students", conn)
    if not df_students.empty:
        student_name = st.selectbox("Select Student", df_students['name'].tolist())
        
        if student_name:
            student_id = pd.read_sql_query("SELECT student_id FROM students WHERE name=?", conn, params=(student_name,))['student_id'].iloc[0]
            
            st.subheader("Academic Performance")
            df_grades = pd.read_sql_query("SELECT * FROM assessments WHERE student_id=?", conn, params=(student_id,))
            if not df_grades.empty:
                st.dataframe(df_grades)
                
                fig_grades = px.line(df_grades, x='date', y='marks', color='subject', 
                                    title='Academic Performance Trend')
                st.plotly_chart(fig_grades)
            else:
                st.info("No assessment data available for this student.")
            
            st.subheader("Attendance Record")
            df_attendance = pd.read_sql_query("SELECT * FROM attendance WHERE student_id=?", conn, params=(student_id,))
            if not df_attendance.empty:
                st.dataframe(df_attendance[['date', 'status', 'behaviour_score']])
                
                # Attendance summary
                present_count = (df_attendance['status'] == 'Present').sum()
                total_count = len(df_attendance)
                attendance_percentage = (present_count / total_count * 100) if total_count > 0 else 0
                
                st.metric("Overall Attendance Rate", f"{attendance_percentage:.1f}%")
            else:
                st.info("No attendance data available for this student.")
    else:
        st.warning("No students available. Please add students first.")

# ===================== EXPORT DATA =====================
elif menu == "Export Data":
    st.header("📥 Export Data")
    
    df_schools = pd.read_sql_query("SELECT * FROM schools", conn)
    if not df_schools.empty:
        school_select = st.selectbox("Select School to Export Data From", df_schools['name'])
        school_id = df_schools[df_schools['name'] == school_select]['school_id'].values[0]
        
        df_students = pd.read_sql_query("SELECT * FROM students WHERE school_id=?", conn, params=(school_id,))
        df_attendance = pd.read_sql_query("SELECT * FROM attendance WHERE school_id=?", conn, params=(school_id,))
        df_assessments = pd.read_sql_query("SELECT * FROM assessments WHERE school_id=?", conn, params=(school_id,))
        df_teachers = pd.read_sql_query("SELECT * FROM teachers WHERE school_id=?", conn, params=(school_id,))
        df_assignments = pd.read_sql_query("SELECT * FROM teacher_assignments WHERE school_id=?", conn, params=(school_id,))

        st.write(f"### 📊 Data Summary for {school_select}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Students", len(df_students))
        with col2:
            st.metric("Teachers", len(df_teachers))
        with col3:
            st.metric("Attendance Records", len(df_attendance))
        with col4:
            st.metric("Assessment Records", len(df_assessments))

        if st.button("📁 Generate Complete Excel Report"):
            try:
                excel_file = f"{school_select}_Complete_Report.xlsx"
                
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    # All data sheets
                    df_students.to_excel(writer, sheet_name='Students', index=False)
                    
                    if not df_attendance.empty:
                        df_attendance.to_excel(writer, sheet_name='Attendance', index=False)
                    else:
                        pd.DataFrame(columns=['attendance_id', 'student_id', 'school_id', 'date', 'status', 'behaviour_score', 'behaviour_comment']).to_excel(writer, sheet_name='Attendance', index=False)
                    
                    if not df_assessments.empty:
                        df_assessments.to_excel(writer, sheet_name='Assessments', index=False)
                    else:
                        pd.DataFrame(columns=['assessment_id', 'student_id', 'school_id', 'date', 'subject', 'marks', 'total', 'grade']).to_excel(writer, sheet_name='Assessments', index=False)
                    
                    if not df_teachers.empty:
                        df_teachers.to_excel(writer, sheet_name='Teachers', index=False)
                    else:
                        pd.DataFrame(columns=['teacher_id', 'school_id', 'name', 'email', 'phone', 'subject', 'qualification', 'join_date', 'status']).to_excel(writer, sheet_name='Teachers', index=False)
                    
                    if not df_assignments.empty:
                        df_assignments.to_excel(writer, sheet_name='Assignments', index=False)
                    else:
                        pd.DataFrame(columns=['assignment_id', 'teacher_id', 'school_id', 'class_grade', 'subject', 'academic_year']).to_excel(writer, sheet_name='Assignments', index=False)
                    
                    # Summary sheet
                    summary_data = {
                        'Metric': [
                            'Total Students', 'Total Teachers', 'Total Attendance Records', 
                            'Total Assessment Records', 'Average Attendance Rate',
                            'Average Behaviour Score', 'Average Marks'
                        ],
                        'Value': [
                            len(df_students), len(df_teachers), len(df_attendance),
                            len(df_assessments),
                            f"{(len(df_attendance[df_attendance['status'] == 'Present']) / len(df_attendance) * 100):.1f}%" if not df_attendance.empty else "N/A",
                            f"{df_attendance['behaviour_score'].mean():.1f}/5" if not df_attendance.empty else "N/A",
                            f"{df_assessments['marks'].mean():.1f}%" if not df_assessments.empty else "N/A"
                        ]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

                with open(excel_file, 'rb') as f:
                    excel_data = f.read()

                st.download_button(
                    label="⬇️ Download Complete Excel Report",
                    data=excel_data,
                    file_name=excel_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.success("✅ Complete Excel report generated successfully!")
                
            except Exception as e:
                st.error(f"Error generating Excel file: {e}")

    else:
        st.warning("No schools available to export data from.")

# ===================== SYSTEM ADMIN =====================
elif menu == "System Admin":
    st.header("⚙️ System Administration")
    
    st.warning("⚠️ These actions are irreversible! Proceed with caution.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Database Status")
        try:
            school_count = pd.read_sql_query("SELECT COUNT(*) as count FROM schools", conn)['count'].iloc[0]
            teacher_count = pd.read_sql_query("SELECT COUNT(*) as count FROM teachers", conn)['count'].iloc[0]
            student_count = pd.read_sql_query("SELECT COUNT(*) as count FROM students", conn)['count'].iloc[0]
            attendance_count = pd.read_sql_query("SELECT COUNT(*) as count FROM attendance", conn)['count'].iloc[0]
            assessment_count = pd.read_sql_query("SELECT COUNT(*) as count FROM assessments", conn)['count'].iloc[0]
            
            st.metric("Schools", school_count)
            st.metric("Teachers", teacher_count)
            st.metric("Students", student_count)
            st.metric("Attendance Records", attendance_count)
            st.metric("Assessment Records", assessment_count)
        except:
            st.error("Error reading database status")
    
    with col2:
        st.subheader("🔄 Reset Options")
        
        if st.button("🗑️ Delete All Students", type="secondary"):
            cursor.execute("DELETE FROM students")
            cursor.execute("DELETE FROM attendance")
            cursor.execute("DELETE FROM assessments")
            conn.commit()
            st.success("All students and related data deleted!")
            st.rerun()
            
        if st.button("👨‍🏫 Delete All Teachers", type="secondary"):
            cursor.execute("DELETE FROM teachers")
            cursor.execute("DELETE FROM teacher_assignments")
            conn.commit()
            st.success("All teachers and related data deleted!")
            st.rerun()
            
        if st.button("🏫 Delete All Schools", type="secondary"):
            cursor.execute("DELETE FROM schools")
            cursor.execute("DELETE FROM students")
            cursor.execute("DELETE FROM attendance")
            cursor.execute("DELETE FROM assessments")
            cursor.execute("DELETE FROM teachers")
            cursor.execute("DELETE FROM teacher_assignments")
            conn.commit()
            st.success("All schools and related data deleted!")
            st.rerun()
    
    with col3:
        st.subheader("💀 Nuclear Option")
        st.error("This will delete EVERYTHING!")
        
        reset_confirmed = st.checkbox("I understand this will delete all data permanently")
        
        if st.button("💥 Reset Entire System", disabled=not reset_confirmed, type="primary"):
            try:
                cursor.execute("DROP TABLE IF EXISTS schools")
                cursor.execute("DROP TABLE IF EXISTS students")
                cursor.execute("DROP TABLE IF EXISTS attendance")
                cursor.execute("DROP TABLE IF EXISTS assessments")
                cursor.execute("DROP TABLE IF EXISTS teachers")
                cursor.execute("DROP TABLE IF EXISTS teacher_assignments")
                
                # Recreate all tables
                cursor.execute('''
                CREATE TABLE schools (
                    school_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER,
                    name TEXT,
                    age INTEGER,
                    grade TEXT,
                    parent_name TEXT,
                    parent_contact TEXT,
                    FOREIGN KEY(school_id) REFERENCES schools(school_id)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE attendance (
                    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    school_id INTEGER,
                    date TEXT,
                    status TEXT,
                    behaviour_score INTEGER,
                    behaviour_comment TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(school_id) REFERENCES schools(school_id)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE assessments (
                    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    school_id INTEGER,
                    date TEXT,
                    subject TEXT,
                    marks INTEGER,
                    total INTEGER,
                    grade TEXT,
                    FOREIGN KEY(student_id) REFERENCES students(student_id),
                    FOREIGN KEY(school_id) REFERENCES schools(school_id)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE teachers (
                    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    subject TEXT,
                    qualification TEXT,
                    join_date TEXT,
                    status TEXT DEFAULT 'Active',
                    FOREIGN KEY(school_id) REFERENCES schools(school_id)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE teacher_assignments (
                    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    teacher_id INTEGER,
                    school_id INTEGER,
                    class_grade TEXT,
                    subject TEXT,
                    academic_year TEXT,
                    FOREIGN KEY(teacher_id) REFERENCES teachers(teacher_id),
                    FOREIGN KEY(school_id) REFERENCES schools(school_id)
                )
                ''')
                
                conn.commit()
                st.success("✅ System reset successfully! All data has been deleted.")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error resetting system: {e}")
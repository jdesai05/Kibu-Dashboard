import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date

from dotenv import load_dotenv
import os

load_dotenv()

# Backend fetch functions
from teachers_database_fetch import (
    fetch_schools,
    fetch_teachers_by_school,
    fetch_school_activity_stats,
    fetch_teacher_activity_count,
    fetch_activities_by_teacher
)


# ---------------------------------------------
# SUPABASE CONFIG
# ---------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

# ---------------------------------------------
# UI COMPONENTS
# ---------------------------------------------
def school_selector(supabase):
    schools = fetch_schools(supabase)

    if not schools:
        st.warning("No schools found.")
        return None

    school_map = {s["school_name"]: s["id"] for s in schools}

    options = ["Select School"] + list(school_map.keys())

    selected = st.selectbox("Select a School", options)

    if selected == "Select School":
        return None

    return school_map[selected]


def teacher_selector(supabase, school_id):
    teachers = fetch_teachers_by_school(supabase, school_id)

    if not teachers:
        st.warning("No teachers found for this school.")
        return None

    teacher_map = {
        f"{t['first_name']} {t['last_name']} ({t['email']})": t["id"]
        for t in teachers
    }

    options = ["Select Teacher"] + list(teacher_map.keys())

    selected = st.selectbox("Select a Teacher", options)

    if selected == "Select Teacher":
        return None

    return teacher_map[selected]


# ---------------------------------------------
# ANALYTICS PAGES
# ---------------------------------------------
def teachers_analytics_page():
    st.header("Teachers Analytics")

    # -------------------------------
    # Date Filters
    # -------------------------------
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", value=None)

    with col2:
        end_date = st.date_input("End Date", value=None)

    if start_date and end_date and start_date > end_date:
        st.error("Start date cannot be after end date.")
        return

    # -------------------------------
    # School Selection
    # -------------------------------
    school_id = school_selector(supabase)

    if not school_id:
        st.info("Please select a school to view analytics.")
        return

    # -------------------------------
    # Overall School Analytics
    # -------------------------------
    stats = fetch_school_activity_stats(
        supabase,
        school_id,
        start_date=start_date,
        end_date=end_date
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Activities (School)",
        stats["total_activities"]
    )

    col2.metric(
        "Median Activities per Teacher",
        stats["median_activities_per_teacher"]
    )

    st.divider()

    # -------------------------------
    # Teacher Selection
    # -------------------------------
    teacher_id = teacher_selector(supabase, school_id)

    if not teacher_id:
        st.info("Select a teacher to view teacher-level analytics.")
        return

    # -------------------------------
    # Teacher-Level Analytics
    # -------------------------------
    teacher_total = fetch_teacher_activity_count(
        supabase,
        teacher_id,
        start_date=start_date,
        end_date=end_date
    )

    st.metric(
        "Total Activities by Selected Teacher",
        teacher_total
    )

    # -------------------------------
    # Teacher Activities Table
    # -------------------------------
    activities = fetch_activities_by_teacher(
        supabase,
        teacher_id,
        start_date=start_date,
        end_date=end_date
    )

    if not activities:
        st.info("No activities found for this teacher in the selected timeframe.")
        return

    df = pd.DataFrame(activities)

    df = df[["name", "subject", "created_at"]]
    df.columns = ["Title", "Subject", "Created At"]

    st.subheader("Activities Created by Teacher")
    st.dataframe(df, use_container_width=True)


def students_analytics_page():
    st.header("Student Analytics")

    # --------------------------------------------------
    # Date Filters
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", value=None)

    with col2:
        end_date = st.date_input("End Date", value=None)

    if start_date and end_date and start_date > end_date:
        st.error("Start date cannot be after end date.")
        return

    # --------------------------------------------------
    # School Selection
    # --------------------------------------------------
    school_id = school_selector(supabase)

    if not school_id:
        st.info("Please select a school to view student analytics.")
        return

    # --------------------------------------------------
    # SCHOOL-LEVEL STUDENT ANALYTICS
    # --------------------------------------------------
    from students_database_fetch import (
        fetch_school_student_stats,
        fetch_published_activities_by_school,
        fetch_activity_student_stats
    )

    school_stats = fetch_school_student_stats(
        supabase,
        school_id,
        start_date=start_date,
        end_date=end_date
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Activities Posted",
        school_stats["total_activities_posted"]
    )

    col2.metric(
        "Sessions Attempted",
        school_stats["total_sessions_attempted"]
    )

    col3.metric(
        "Completion Rate",
        f"{school_stats['completion_rate']:.1f}%"
    )

    col4.metric(
        "Avg Time Spent (Minutes)",
        round(school_stats["mean_time_spent"], 1)
    )

    st.caption(
        f"Median Time Spent: {round(school_stats['median_time_spent'], 1)} Minutes"
    )

    st.divider()

    # --------------------------------------------------
    # ACTIVITY SELECTION (Published only)
    # --------------------------------------------------
    published_activities = fetch_published_activities_by_school(
        supabase,
        school_id,
        start_date=start_date,
        end_date=end_date
    )

    if not published_activities:
        st.info("No published activities found for this school.")
        return

    activity_map = {
        f"{a['name']} ({a['id']})": a["id"]
        for a in published_activities
    }

    options = ["Select Activity"] + list(activity_map.keys())

    selected_activity = st.selectbox(
        "Select an Activity",
        options
    )

    if selected_activity == "Select Activity":
        st.info("Select an activity to view activity-level stats.")
        return

    activity_id = activity_map[selected_activity]

    # --------------------------------------------------
    # ACTIVITY-LEVEL STUDENT ANALYTICS
    # --------------------------------------------------
    activity_stats = fetch_activity_student_stats(
        supabase,
        school_id,
        activity_id,
        start_date=start_date,
        end_date=end_date
    )

    st.subheader("Activity-Level Student Analytics")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Sessions Attempted",
        activity_stats["total_sessions_attempted"]
    )

    col2.metric(
        "Completion Rate",
        f"{activity_stats['completion_rate']:.1f}%"
    )

    col3.metric(
        "Avg Time Spent (Minutes)",
        round(activity_stats["mean_time_spent"], 1)
    )

    st.caption(
        f"Median Time Spent: {round(activity_stats['median_time_spent'], 1)} Minutes"
    )


def study_material_analytics_page():
    st.header("Study Material Analytics")
    st.info("🚧 Coming soon")


# ---------------------------------------------
# MAIN APP
# ---------------------------------------------
def main():
    st.set_page_config(
        page_title="School Analytics Dashboard",
        layout="wide"
    )

    st.sidebar.title("Analytics Dashboard")

    selected_page = st.sidebar.radio(
        "Select Analytics View",
        [
            "Teachers Analytics",
            "Student Analytics",
            "Study Material Analytics"
        ]
    )

    if selected_page == "Teachers Analytics":
        teachers_analytics_page()

    elif selected_page == "Student Analytics":
        students_analytics_page()

    elif selected_page == "Study Material Analytics":
        study_material_analytics_page()


if __name__ == "__main__":
    main()
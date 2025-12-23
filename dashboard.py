import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date
from comparative_analysis import compare_school_performance
from teachers_database_fetch import fetch_schools
import plotly.graph_objects as go
from add_new_school import insert_school


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

from study_materials_database_fetch import fetch_study_material_stats


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


def render_comparison_bar_chart(title, period_a_value, period_b_value, y_label):
    fig = go.Figure(
        data = [
            go.Bar(
                name="Period A",
                x=["Period A"],
                y=[period_a_value],
                text=[round(period_a_value, 2)],
                textposition="auto",
            ),
            go.Bar(
                name="Period B",
                x=["Period B"],
                y=[period_b_value],
                text=[round(period_b_value, 2)],
                textposition="auto",
            ),
        ]
    )

    fig.update_layout(
        title=title,
        yaxis_title=y_label,
        xaxis_title="",
        barmode="group",
        height=350,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)



def comparative_analysis():
    st.header("Comparative Analysis")

    # --------------------------------------------------
    # PERIOD SELECTION
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Period A (Baseline)")
        start_a = st.date_input("Start Date A", key="ca_start_a")
        end_a = st.date_input("End Date A", key="ca_end_a")

    with col2:
        st.markdown("### Period B (Comparison)")
        start_b = st.date_input("Start Date B", key="ca_start_b")
        end_b = st.date_input("End Date B", key="ca_end_b")

    if start_a > end_a or start_b > end_b:
        st.error("Start date cannot be after end date.")
        return

    # --------------------------------------------------
    # SCHOOL SELECTION
    # --------------------------------------------------
    schools = fetch_schools(supabase)

    if not schools:
        st.warning("No schools found.")
        return

    school_map = {s["school_name"]: s["id"] for s in schools}
    selected_school = st.selectbox(
        "Select School",
        ["Select School"] + list(school_map.keys())
    )

    if selected_school == "Select School":
        st.info("Select a school to compare performance.")
        return

    school_id = school_map[selected_school]

    # --------------------------------------------------
    # RUN COMPARISON
    # --------------------------------------------------
    with st.spinner("Running comparative analysis..."):
        comparison = compare_school_performance(
            supabase=supabase,
            school_id=school_id,
            period_a={"start": start_a, "end": end_a},
            period_b={"start": start_b, "end": end_b},
        )

    teachers = comparison["teachers"]
    students = comparison["students"]

    # --------------------------------------------------
    # TEACHERS COMPARISON
    # --------------------------------------------------
    st.subheader("Teachers Comparison")

    col1, col2 = st.columns(2)

    t_total = teachers["total_activities"]
    t_median = teachers["median_activities_per_teacher"]

    col1.metric(
        "Total Activities Created",
        t_total["new"],
        f"{t_total['absolute']:+} "
        f"({t_total['percentage']:+.1f}%)"
        if t_total["percentage"] is not None else f"{t_total['absolute']:+}"
    )

    col2.metric(
        "Median Activities per Teacher",
        t_median["new"],
        f"{t_median['absolute']:+} "
        f"({t_median['percentage']:+.1f}%)"
        if t_median["percentage"] is not None else f"{t_median['absolute']:+}"
    )

    # --------------------------------------------------
    # STUDENTS COMPARISON
    # --------------------------------------------------
    st.subheader("Students Comparison")

    col1, col2, col3 = st.columns(3)

    s_sessions = students["total_sessions_attempted"]
    s_completion = students["completion_rate"]
    s_time = students["mean_time_spent"]

    col1.metric(
        "Sessions Attempted",
        s_sessions["new"],
        f"{s_sessions['absolute']:+} "
        f"({s_sessions['percentage']:+.1f}%)"
        if s_sessions["percentage"] is not None else f"{s_sessions['absolute']:+}"
    )

    col2.metric(
        "Completion Rate (%)",
        f"{s_completion['new']:.1f}",
        f"{s_completion['absolute']:+.1f} "
        f"({s_completion['percentage']:+.1f}%)"
        if s_completion["percentage"] is not None else f"{s_completion['absolute']:+.1f}"
    )

    col3.metric(
        "Avg Time Spent (min)",
        f"{s_time['new']:.2f}",
        f"{s_time['absolute']:+.2f} "
        f"({s_time['percentage']:+.1f}%)"
        if s_time["percentage"] is not None else f"{s_time['absolute']:+.2f}"
    )

    st.caption(
        f"Median Time Spent (min): "
        f"{students['median_time_spent']['old']:.2f} → "
        f"{students['median_time_spent']['new']:.2f}"
    )

     # --------------------------------------------------
    # BAR CHART COMPARISONS
    # --------------------------------------------------
    st.subheader("A vs B Visual Comparison")

    st.markdown("### Teachers")

    render_comparison_bar_chart(
        title="Total Activities Created",
        period_a_value=t_total["old"],
        period_b_value=t_total["new"],
        y_label="Activities",
    )

    render_comparison_bar_chart(
        title="Median Activities per Teacher",
        period_a_value=t_median["old"],
        period_b_value=t_median["new"],
        y_label="Activities",
    )

    st.markdown("### Students")

    render_comparison_bar_chart(
        title="Total Sessions Attempted",
        period_a_value=s_sessions["old"],
        period_b_value=s_sessions["new"],
        y_label="Sessions",
    )

    render_comparison_bar_chart(
        title="Completion Rate (%)",
        period_a_value=s_completion["old"],
        period_b_value=s_completion["new"],
        y_label="Percentage",
    )

    render_comparison_bar_chart(
        title="Mean Time Spent (minutes)",
        period_a_value=s_time["old"],
        period_b_value=s_time["new"],
        y_label="Minutes",
    )


def add_new_school_form():
    st.subheader("Add New School")

    with st.form("add_school_form", clear_on_submit=True):
        school_name = st.text_input("School Name *")
        subdomain = st.text_input("Subdomain *")
        admin_mail = st.text_input("Admin Email *")

        address = st.text_area("Address")
        city = st.text_input("City")
        state = st.text_input("State")
        country = st.text_input("Country")
        postal_code = st.text_input("Postal Code")

        board_id = st.text_input("Board ID")
        is_active = st.checkbox("Is Active", value=True)

        submitted = st.form_submit_button("Create School")

        if submitted:
            # -------------------------------
            # Manual validation
            # -------------------------------
            if not school_name.strip():
                st.error("School Name is required.")
                return

            if not subdomain.strip():
                st.error("Subdomain is required.")
                return

            if not admin_mail.strip():
                st.error("Admin Email is required.")
                return

            try:
                insert_school(
                    supabase=supabase,
                    school_name=school_name.strip(),
                    subdomain=subdomain.strip(),
                    admin_mail=admin_mail.strip(),
                    address=address.strip(),
                    city=city.strip(),
                    state=state.strip(),
                    country=country.strip(),
                    postal_code=postal_code.strip(),
                    is_active=is_active,
                    board_id=board_id.strip() if board_id else None,
                )

                st.success("✅ School added successfully!")
                st.info("You may need to refresh to see it in dropdowns.")

            except Exception as e:
                st.error(f"❌ Failed to add school: {str(e)}")



def study_material_analytics_page():
    st.header("Study Material Analytics")

    # --------------------------------------------------
    # DATE FILTERS (OPTIONAL)
    # --------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=None,
            key="sm_start_date"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=None,
            key="sm_end_date"
        )

    if start_date and end_date and start_date > end_date:
        st.error("Start date cannot be after end date.")
        return

    # --------------------------------------------------
    # SCHOOL SELECTION
    # --------------------------------------------------
    schools = fetch_schools(supabase)

    if not schools:
        st.warning("No schools found.")
        return

    school_map = {s["school_name"]: s["id"] for s in schools}

    selected_school = st.selectbox(
        "Select School",
        ["Select School"] + list(school_map.keys())
    )

    if selected_school == "Select School":
        st.info("Please select a school to view study material analytics.")
        return

    school_id = school_map[selected_school]

    # --------------------------------------------------
    # FETCH STATS
    # --------------------------------------------------
    with st.spinner("Fetching study material analytics..."):
        stats = fetch_study_material_stats(
            supabase,
            school_id,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None
        )

    # --------------------------------------------------
    # KPI METRICS
    # --------------------------------------------------
    st.subheader("Usage Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Flashcards Used", stats["flashcards_count"])
    col2.metric("Quizzes Used", stats["quiz_count"])
    col3.metric("Total Tool Runs", stats["total_runs"])
    col4.metric("Failure Rate", f"{stats['failure_percentage']:.1f}%")

    # --------------------------------------------------
    # CONTEXTUAL INSIGHT
    # --------------------------------------------------
    st.divider()

    if stats["total_runs"] == 0:
        st.info("No study material usage recorded for the selected period.")
    else:
        if stats["failure_percentage"] > 30:
            st.warning(
                "⚠️ A high percentage of study material attempts failed. "
                "Consider reviewing content difficulty or clarity."
            )
        else:
            st.success(
                "✅ Study material usage is healthy with an acceptable failure rate."
            )

# ---------------------------------------------
# MAIN APP
# ---------------------------------------------
def main():
    st.set_page_config(
        page_title="School Analytics Dashboard",
        layout="wide"
    )

    # ---------------------------------------------
    # SIDEBAR
    # ---------------------------------------------
    st.sidebar.title("Analytics Dashboard")

    selected_page = st.sidebar.radio(
        "Select Analytics View",
        [
            "Teachers Analytics",
            "Student Analytics",
            "Comparative Analysis",
            "Study Material Analytics"
        ]
    )

    # Spacer to push button to bottom
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    st.sidebar.divider()

    if st.sidebar.button("➕ Add New School"):
        st.session_state["show_add_school"] = True
        st.session_state["selected_page_override"] = None

    # ---------------------------------------------
    # MAIN CONTENT
    # ---------------------------------------------
    # If Add School is triggered, show form
    if st.session_state.get("show_add_school"):
        add_new_school_form()

        # Optional: Back button
        if st.button("⬅ Back to Dashboard"):
            st.session_state["show_add_school"] = False
            st.rerun()

        return  # stop rendering analytics pages

    # ---------------------------------------------
    # PAGE ROUTING
    # ---------------------------------------------
    if selected_page == "Teachers Analytics":
        teachers_analytics_page()

    elif selected_page == "Student Analytics":
        students_analytics_page()

    elif selected_page == "Comparative Analysis":
        comparative_analysis()

    elif selected_page == "Study Material Analytics":
        study_material_analytics_page()


if __name__ == "__main__":
    main()

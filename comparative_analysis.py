import streamlit as st
from datetime import date
from typing import Dict
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import pandas as pd

from teachers_database_fetch import fetch_school_activity_stats
from students_database_fetch import fetch_school_student_stats

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

def calculate_delta(old: float, new: float) -> dict:
    """
    Computes delta metrics between two values.

    Returns a stable contract used by frontend:
    {
        old: float,
        new: float,
        absolute: float,
        percentage: float | None
    }
    """
    absolute = new - old

    percentage = None
    if old != 0:
        percentage = (absolute / old) * 100

    return {
        "old": old,
        "new": new,
        "absolute": absolute,
        "percentage": percentage
    }


def render_metric(lavel, val_a, val_b):
    delta = calculate_delta(delta["absolute"], float)

    delta_str = (
        f"{delta['absolute']:+.2f}"
        if isinstance(delta["absolute"], float)
        else f"{delta['absolute']:+}"
    )

    delta_str = (
        f"{delta['absolute']:+.2f}"
        if isinstance(delta["absolute"], float)
        else f"{delta['absolute']:+}"
    )


def compare_teacher_stats(
        supabase,
        school_id, 
        start_a: date,
        end_a: date,
        start_b: date,
        end_b: date
    ) -> Dict:

    stats_a = fetch_school_activity_stats(supabase, school_id, start_date=start_a, end_date=end_a)

    stats_b = fetch_school_activity_stats(supabase, school_id, start_date=start_b, end_date=end_b)

    return {
        "total_activities": calculate_delta(
            stats_a["total_activities"],
            stats_b["total_activities"]
        ),
        "median_activities_per_teacher": calculate_delta(
            stats_a["total_activities"],
            stats_b["total_activities"]
        )
    }


def compare_student_stats(
        supabase,
        school_id,
        start_a: date,
        end_a: date,
        start_b: date,
        end_b: date
    ) -> Dict:
    stats_a = fetch_school_student_stats(
        supabase,
        school_id,
        start_date=start_a,
        end_date=end_a
    )

    stats_b = fetch_school_student_stats(
        supabase,
        school_id,
        start_date=start_b,
        end_date=end_b
    )

    return {
        "total_activities_posted": calculate_delta(
            stats_a["total_activities_posted"],
            stats_b["total_activities_posted"]
        ),
        "total_sessions_attempted": calculate_delta(
            stats_a["total_sessions_attempted"],
            stats_b["total_sessions_attempted"]
        ),
        "completion_rate": calculate_delta(
            stats_a["completion_rate"],
            stats_b["completion_rate"]
        ),
        "mean_time_spent": calculate_delta(
            stats_a["mean_time_spent"],
            stats_b["mean_time_spent"]
        ),
        "median_time_spent": calculate_delta(
            stats_a["median_time_spent"],
            stats_b["median_time_spent"]
        )
    }

# --------------------------------------------------
# MASTER COMPARISON (TEACHERS + STUDENTS)
# --------------------------------------------------
def compare_school_performance(
    supabase,
    school_id,
    period_a: Dict[str, date],
    period_b: Dict[str, date]
) -> Dict:
    """
    Compare school performance across two periods.

    period_a = { "start": date, "end": date }
    period_b = { "start": date, "end": date }
    """

    teacher_comparison = compare_teacher_stats(
        supabase,
        school_id,
        period_a["start"],
        period_a["end"],
        period_b["start"],
        period_b["end"]
    )

    student_comparison = compare_student_stats(
        supabase,
        school_id,
        period_a["start"],
        period_a["end"],
        period_b["start"],
        period_b["end"]
    )

    return {
        "teachers": teacher_comparison,
        "students": student_comparison
    }


def render_comparison_bar_chart(title, value_a, value_b, unit=None):
    """
    Renders a simple A vs B bar chart.
    """
    df = pd.DataFrame(
        {
            "Period": ["Period A", "Period B"],
            "Value": [value_a, value_b]
        }
    )

    st.markdown(f"#### {title}")
    st.bar_chart(
        df.set_index("Period"),
        y="Value"
    )

    if unit:
        st.caption(f"Unit: {unit}")
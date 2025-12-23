from supabase import create_client, Client
from datetime import date, datetime, time
from typing import Optional, List, Dict
import statistics

from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

# --------------------------------------------------
# PUBLISHED ACTIVITIES (for dropdown)
# --------------------------------------------------
def fetch_published_activities_by_school(
    supabase,
    school_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict]:
    """
    Returns published activities for a school.
    Used for activity dropdown.
    """

    # Step 1: fetch activities for school
    query = (
        supabase
        .table("activities")
        .select("id, name")
        .eq("school_id", school_id)
    )

    if start_date:
        query = query.gte("created_at", start_date.isoformat())
    if end_date:
        query = query.lte("created_at", end_date.isoformat())

    activities = query.execute().data or []

    if not activities:
        return []

    activity_ids = [a["id"] for a in activities]

    # Step 2: filter published activities
    published = (
        supabase
        .table("published_activities")
        .select("activity_id")
        .in_("activity_id", activity_ids)
        .execute()
        .data or []
    )

    published_ids = {p["activity_id"] for p in published}

    return [
        a for a in activities if a["id"] in published_ids
    ]


# --------------------------------------------------
# ACTIVITY SESSIONS FETCH
# --------------------------------------------------
def fetch_activity_sessions(
    supabase,
    school_id,
    activity_ids: List,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict]:

    if not activity_ids:
        return []

    query = (
        supabase
        .table("activity_sessions")
        .select("activity_id, start_time, end_time, created_at, status")
        .eq("school_id", school_id)
        .in_("activity_id", activity_ids)
    )

    if start_date:
        query = query.gte("created_at", start_date.isoformat())
    if end_date:
        query = query.lte("created_at", end_date.isoformat())

    return query.execute().data or []


# --------------------------------------------------
# UTILITY: TIME CALCULATION
# --------------------------------------------------
def _extract_durations(sessions):
    durations = []

    for s in sessions:
        start_raw = s.get("start_time")
        end_raw = s.get("end_time")
        created_raw = s.get("created_at")

        if not start_raw or not end_raw or not created_raw:
            continue

        try:
            # Parse created_at (date source)
            created_dt = datetime.fromisoformat(
                created_raw.replace("Z", "+00:00")
            )
            base_date = created_dt.date()

            # Parse time-only fields
            start_t = time.fromisoformat(start_raw)
            end_t = time.fromisoformat(end_raw)

            # Combine date + time
            start_dt = datetime.combine(base_date, start_t)
            end_dt = datetime.combine(base_date, end_t)

        except Exception:
            continue

        # Handle cross-midnight sessions (rare but possible)
        if end_dt < start_dt:
            end_dt = end_dt.replace(day=end_dt.day + 1)

        durations.append((end_dt - start_dt).total_seconds() / 60)

    return durations


# --------------------------------------------------
# SCHOOL-LEVEL STUDENT ANALYTICS
# --------------------------------------------------
def fetch_school_student_stats(
    supabase,
    school_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:

    published_activities = fetch_published_activities_by_school(
        supabase, school_id, start_date, end_date
    )

    activity_ids = [a["id"] for a in published_activities]

    sessions = fetch_activity_sessions(
        supabase, school_id, activity_ids, start_date, end_date
    )

    durations = _extract_durations(sessions)

    total_sessions = len(sessions)
    completed_sessions = sum(
        1 for s in sessions if s["status"] in ("completed", "active")
    )

    return {
        "total_activities_posted": len(activity_ids),
        "total_sessions_attempted": total_sessions,
        "completion_rate": (
            completed_sessions / total_sessions * 100
            if total_sessions else 0
        ),
        "mean_time_spent": (
            statistics.mean(durations) if durations else 0
        ),
        "median_time_spent": (
            statistics.median(durations) if durations else 0
        )
    }


# --------------------------------------------------
# ACTIVITY-LEVEL STUDENT ANALYTICS
# --------------------------------------------------
def fetch_activity_student_stats(
    supabase,
    school_id,
    activity_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:

    sessions = fetch_activity_sessions(
        supabase,
        school_id,
        [activity_id],
        start_date,
        end_date
    )

    durations = _extract_durations(sessions)

    total_sessions = len(sessions)
    completed_sessions = sum(
        1 for s in sessions if s["status"] in ("completed", "active")
    )

    return {
        "total_sessions_attempted": total_sessions,
        "completion_rate": (
            completed_sessions / total_sessions * 100
            if total_sessions else 0
        ),
        "mean_time_spent": (
            statistics.mean(durations) if durations else 0
        ),
        "median_time_spent": (
            statistics.median(durations) if durations else 0
        )
    }
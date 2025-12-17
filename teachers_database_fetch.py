from supabase import create_client, Client
from datetime import date
from typing import Optional, Dict, List

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
# SCHOOLS
# --------------------------------------------------
def fetch_schools(supabase) -> List[Dict]:
    """
    Fetch all schools (id + name).
    """
    response = (
        supabase
        .table("schools")
        .select("id, school_name")
        .order("school_name", desc=False)
        .execute()
    )

    return response.data or []


# --------------------------------------------------
# TEACHERS
# --------------------------------------------------
def fetch_teachers_by_school(supabase, school_id) -> List[Dict]:
    """
    Fetch all teachers for a given school.
    """
    response = (
        supabase
        .table("profiles")
        .select("id, first_name, last_name, email")
        .eq("school_id", school_id)
        .eq("role", "teacher")
        .order("first_name", desc=False)
        .execute()
    )

    return response.data or []


# --------------------------------------------------
# ACTIVITIES (TEACHER LEVEL)
# --------------------------------------------------
def fetch_activities_by_teacher(
    supabase,
    teacher_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Dict]:
    """
    Fetch activities created by a teacher with optional date filtering.
    """

    query = (
        supabase
        .table("activities")
        .select("id, name, subject, created_at")
        .eq("creator_id", teacher_id)
    )

    if start_date:
        query = query.gte("created_at", start_date.isoformat())

    if end_date:
        query = query.lte("created_at", end_date.isoformat())

    response = (
        query
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


# --------------------------------------------------
# SCHOOL-LEVEL ANALYTICS
# --------------------------------------------------
def fetch_school_activity_stats(
    supabase,
    school_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict:
    """
    Returns:
    - total_activities
    - median_activities_per_teacher
    """

    query = (
        supabase
        .table("activities")
        .select("creator_id")
        .eq("school_id", school_id)
    )

    if start_date:
        query = query.gte("created_at", start_date.isoformat())

    if end_date:
        query = query.lte("created_at", end_date.isoformat())

    response = query.execute()

    data = response.data or []

    if not data:
        return {
            "total_activities": 0,
            "median_activities_per_teacher": 0
        }

    # Count activities per teacher
    teacher_counts = {}
    for row in data:
        teacher_id = row["creator_id"]
        teacher_counts[teacher_id] = teacher_counts.get(teacher_id, 0) + 1

    counts = sorted(teacher_counts.values())
    total_activities = sum(counts)

    n = len(counts)
    if n % 2 == 1:
        median = counts[n // 2]
    else:
        median = (counts[n // 2 - 1] + counts[n // 2]) / 2

    return {
        "total_activities": total_activities,
        "median_activities_per_teacher": median
    }


# --------------------------------------------------
# TEACHER-LEVEL ANALYTICS
# --------------------------------------------------
def fetch_teacher_activity_count(
    supabase,
    teacher_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    """
    Returns total number of activities created by a teacher.
    """

    query = (
        supabase
        .table("activities")
        .select("id", count="exact")
        .eq("creator_id", teacher_id)
    )

    if start_date:
        query = query.gte("created_at", start_date.isoformat())

    if end_date:
        query = query.lte("created_at", end_date.isoformat())

    response = query.execute()
    return response.count or 0
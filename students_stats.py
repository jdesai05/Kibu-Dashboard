'''
Database functions used to fetch various statistics from the Supabase students database:
1. get_attempted_sessions_count
2. get_total_published_activities
3. get_completed_sessions_count
4. get_ongoing_sessions_count
5. get_completed_session_median_time

'''
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

def fetch_attempted_sessions_count(
        supabase,
        school_id,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> int:
    
    params = {
        "p_school_id":school_id,
        "p_start_date": start_date.isoformat() if start_date else None,
        "p_end_date": end_date.isoformat() if end_date else None,
    }

    response = supabase.rpc(
        "get_attempted_sessions_count",
        params
    ).execute()

    if response.data is None:
        return 0
    
    return response.data

def fetch_total_published_activities(
        supabase,
        school_id, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> int:
    params = {
        "p_school_id": school_id,
        "p_start_date": start_date.isoformat() if start_date else None,
        "p_end_date": end_date.isoformat() if end_date else None,
    }

    response = supabase.rpc(
        "get_total_published_activities",
        params
    ).execute()

    if response.data is None:
        return 0

    return response.data


def fetch_completed_sessions_count(
    supabase,
    school_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    """
    Returns number of completed activity sessions
    for published activities in a school.
    """

    params = {
        "p_school_id": school_id,
        "p_start_date": start_date.isoformat() if start_date else None,
        "p_end_date": end_date.isoformat() if end_date else None,
    }

    response = supabase.rpc(
        "get_completed_sessions_count",
        params
    ).execute()

    if response.data is None:
        return 0

    return response.data


def fetch_ongoing_sessions_count(
    supabase,
    school_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> int:
    """
    Returns number of ongoing (non-completed) activity sessions
    for published activities in a school.
    """

    params = {
        "p_school_id": school_id,
        "p_start_date": start_date.isoformat() if start_date else None,
        "p_end_date": end_date.isoformat() if end_date else None,
    }

    response = supabase.rpc(
        "get_ongoing_sessions_count",
        params
    ).execute()

    if response.data is None:
        return 0

    return response.data


def fetch_completed_session_median_time(
    supabase,
    school_id,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> float:
    """
    Returns median time (in minutes) for COMPLETED sessions
    of published activities.
    """

    params = {
        "p_school_id": school_id,
        "p_start_date": start_date.isoformat() if start_date else None,
        "p_end_date": end_date.isoformat() if end_date else None,
    }

    response = supabase.rpc(
        "get_completed_session_median_time",
        params
    ).execute()

    return float(response.data or 0)


'''
count = fetch_attempted_sessions_count(
    supabase,
    school_id="2a7f8b70-1945-4931-bc65-68bfc37a2d97",
    start_date=date(2025, 9, 1),
    end_date=date(2025, 10, 1)
)

print(count)
'''
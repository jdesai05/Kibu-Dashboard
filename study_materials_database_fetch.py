from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import date
from typing import Dict, Optional

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def fetch_study_material_stats(
        supabase,
        school_id, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
) -> Dict:
    
    response = (
        supabase
        .table("student_tool_runs")
        .select("kind,status")
        .eq("school_id", school_id)
    )

    if start_date:
        response = response.gte("created_at",start_date.isoformat())

    if end_date:
        response = response.lte("created_at",start_date.isoformat())

    query = response.execute()
    data = query.data or []

    flashcards_count = 0
    quiz_count = 0
    total_runs = len(data)
    failed_runs = 0

    for row in data:
        kind = row.get("kind")
        status = row.get("status")

        if kind == "flashcards":
            flashcards_count += 1
        elif kind == "quiz":
            quiz_count += 1

        if status == "failed":
            failed_runs += 1

    failure_percentage = (
        (failed_runs / total_runs) * 100
        if total_runs > 0
        else 0
    )

    return {
        "flashcards_count": flashcards_count,
        "quiz_count": quiz_count,
        "total_runs": total_runs,
        "failed_runs": failed_runs,
        "failure_percentage": failure_percentage,
    }
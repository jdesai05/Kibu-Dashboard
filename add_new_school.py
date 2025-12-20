from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import datetime, time
from typing import Dict

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


supabase: Client = create_client( SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY )

def insert_school(
        supabase, 
        school_name: str, 
        subdomain: str, 
        admin_mail: str, 
        address: str, 
        city: str,
        state: str,
        country: str, 
        postal_code: str, 
        is_active: bool, 
        board_id,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    )-> Dict:
    
    now = datetime.utcnow()

    payload = {
        "school_name": school_name,
        "subdomain": subdomain,
        "admin_mail": admin_mail,
        "address": address,
        "city": city,
        "state": state,
        "country": country,
        "postal code": postal_code,
        "is_active": is_active,
        "board_id": board_id,
    }

    response = (
        supabase
        .table("schools")
        .insert(payload)
        .execute()
    )

    if response.data is None:
        raise Exception("Failed to insert school")

    return response.data[0]
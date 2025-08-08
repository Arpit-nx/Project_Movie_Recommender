import os
from supabase import create_client, Client
from django.conf import settings

# Initialize Supabase client
def get_supabase_client() -> Client:
    """
    Create and return a Supabase client instance
    """
    url = os.getenv('VITE_SUPABASE_URL')
    key = os.getenv('VITE_SUPABASE_ANON_KEY')
    
    if not url or not key:
        raise ValueError("Supabase URL and ANON KEY must be set in environment variables")
    
    return create_client(url, key)

# Global client instance
supabase: Client = get_supabase_client()
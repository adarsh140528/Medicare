"""MediVision AI - Supabase Client with SQLite Fallback"""
import os
from backend.utils.db import SQLiteClient

_client = None
_service_client = None


def get_client():
    """Anon client — falls back to SQLite client if Supabase is unconfigured."""
    global _client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        return SQLiteClient()
    try:
        if _client is None:
            from supabase import create_client
            _client = create_client(url, key)
        return _client
    except Exception as e:
        print(f"[SUPABASE-CLIENT] Falling back to SQLite: {e}")
        return SQLiteClient()


def get_service_client():
    """Service-role client — falls back to SQLite client if Supabase is unconfigured."""
    global _service_client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    if not url or not key:
        return SQLiteClient()
    try:
        anon_key = os.getenv('SUPABASE_KEY', '')
        cached_with_anon = (_service_client is not None and key == anon_key
                            and os.getenv('SUPABASE_SERVICE_KEY'))
        if _service_client is None or cached_with_anon or isinstance(_service_client, SQLiteClient):
            from supabase import create_client
            _service_client = create_client(url, key)
        return _service_client
    except Exception as e:
        print(f"[SUPABASE-SERVICE-CLIENT] Falling back to SQLite: {e}")
        return SQLiteClient()


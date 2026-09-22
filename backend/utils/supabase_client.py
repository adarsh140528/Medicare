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
    """Service-role client — uses service key if valid JWT, else falls back to anon key, else SQLite."""
    global _service_client
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    anon_key = os.getenv('SUPABASE_KEY')

    if not url or not (service_key or anon_key):
        return SQLiteClient()

    # Prefer key that looks like a JWT or valid token
    keys_to_try = []
    if service_key and service_key.startswith('eyJ'):
        keys_to_try.append(service_key)
    if anon_key and anon_key.startswith('eyJ'):
        keys_to_try.append(anon_key)
    if service_key and service_key not in keys_to_try:
        keys_to_try.append(service_key)
    if anon_key and anon_key not in keys_to_try:
        keys_to_try.append(anon_key)

    for k in keys_to_try:
        try:
            from supabase import create_client
            _service_client = create_client(url, k)
            return _service_client
        except Exception:
            continue

    return SQLiteClient()


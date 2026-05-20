"""MediVision AI - Supabase Client"""
import os
from supabase import create_client, Client

_client = None
_service_client = None


def get_client() -> Client:
    """Anon client — use only for public reads (not needed currently)."""
    global _client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        raise Exception("Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_KEY in .env")
    # Re-create if env changed (e.g. on reload); safe because client is stateless
    if _client is None:
        _client = create_client(url, key)
    return _client


def get_service_client() -> Client:
    """Service-role client — bypasses RLS for all server-side operations."""
    global _service_client
    url = os.getenv('SUPABASE_URL')
    # Prefer service key; fall back to anon key if not set
    key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
    if not url or not key:
        raise Exception("Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
    # Always verify the cached client was built with the service key.
    # If SUPABASE_SERVICE_KEY was missing on first call, the singleton would
    # have been created with the anon key and all RLS-protected queries would
    # fail with 500. Re-create whenever the key looks like an anon key.
    anon_key = os.getenv('SUPABASE_KEY', '')
    cached_with_anon = (_service_client is not None and key == anon_key
                        and os.getenv('SUPABASE_SERVICE_KEY'))
    if _service_client is None or cached_with_anon:
        _service_client = create_client(url, key)
    return _service_client
